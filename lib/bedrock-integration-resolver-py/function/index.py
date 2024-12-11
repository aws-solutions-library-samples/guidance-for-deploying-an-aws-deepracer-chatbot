import os
from uuid import uuid4

import boto3
import chains.model_evaluation as model_evaluation_chain
import chains.question_n_answers as question_n_answers_chain
import chains.reward_function_generation as reward_function_generation_chain
import utils.appsync as appsync
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from knowledge_base.vector_db import FaissVectorStore
from track_manager import TrackManager
from utils.chat_history import ChatHistory
from utils.converse_stream import BedrockStream, MessageProcessor, ToolProcessor
from utils.embedding_models import TitanEmbeddings
from utils.model_storage import ModelStorage
from utils.utils import safe_decode_base64

logger = Logger()
app = AppSyncResolver()

# Initiate the ChatHistory persistent store
CHAT_HISTORY_DDB_TABLE_NAME = os.environ["CHAT_HISTORY_DDB_TABLE_NAME"]
chat_history = ChatHistory(table_name=CHAT_HISTORY_DDB_TABLE_NAME)

# Initiate the ModelStorage persistent store
MODEL_STORAGE_DDB_TABLE_NAME = os.environ["MODEL_STORAGE_DDB_TABLE_NAME"]
model_storage = ModelStorage(table_name=MODEL_STORAGE_DDB_TABLE_NAME)

bedrock_runtime_client = boto3.client(service_name="bedrock-runtime")

# Initiate Bedrock converse_stream API
bedrock_stream_model = BedrockStream(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    boto3_client=bedrock_runtime_client,
)

# Initiate the processor to manage the Bedrock converse_stream events
message_processor = MessageProcessor()

# Initiate the embeddings model
embeddings = TitanEmbeddings(
    boto3_client=bedrock_runtime_client, model_id="amazon.titan-embed-image-v1"
)

# Initiate the DeepRacer knowledge vector store
persistant_directory_faiss_knowledge_base = "knowledge_base/deepracer_knowledge"
vector_store_kb = FaissVectorStore.load(
    directory_path=persistant_directory_faiss_knowledge_base,
    embedding_function=embeddings,
)

# Initiate the reward function examples vector store
peristant_directory_faiss_reward_functions = "knowledge_base/reward_function_examples"
vector_store_reward_functions = FaissVectorStore.load(
    directory_path=peristant_directory_faiss_reward_functions,
    embedding_function=embeddings,
)

track_manager = TrackManager()


# Entry point for the lambda function
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def handler(event: dict, context: LambdaContext) -> str:
    """
    The entry point for the Lambda function.

    Args:
        event (dict): The event payload.
        context (LambdaContext): The Lambda context object.

    Returns:
        dict: The response from the AppSync resolver.
    """
    logger.debug(event)

    # Route the event to the corresponding resolver function
    response = app.resolve(event, context)
    return response


# Resolver for calls to the sendMessage Mutation
@app.resolver(type_name="Mutation", field_name="sendMessage")
def sendMessage(chatbotVariant: str, sessionId: str, content):
    """
    Send a message to the chatbot.

    Args:
        message (any): The message to be sent.
        chatbotVariant (any): The variant of the chatbot.
        sessionId (str, optional): The ID of the session. Defaults to "".
        user_id (str, optional): The ID of the user. Defaults to "".

    Returns:
        dict: The response from the chatbot.

    Raises:
        ValueError: If the chatbot variant is invalid.
    """
    identity = app.current_event.get("identity")
    user_id = identity.get("sub")

    logger.append_keys(sessionId=sessionId, userId=user_id)
    logger.debug(
        f"SendMessage Mutation content",
        extra={"content": content, "chatbotVariant": chatbotVariant},
    )
    try:
        # Extract information from the incoming message
        chatbot_variant = chatbotVariant
        session_id = sessionId if sessionId is not None else str(uuid4())

        # Decode base64 encoded images so Bedrock Converse API accepts them as input
        decode_content_images(content)

        # Generate a unique message id to be able to identify the individual messages in a session
        message_id = str(uuid4())

        # Get previous messages in the conversation (if any) from the session store
        conversation = chat_history.load(user_id=user_id, session_id=session_id)

        # Append the current user message to the conversation
        user_message = {"role": "user", "content": content}
        conversation.append(user_message)

        # Initiate the callback to stream the generated text to Appsync
        appsync_callback_handler = appsync.StreamCallbackHandler(
            user_id=user_id,
            session_id=session_id,
            message_id=message_id,
            chatbot_variant=chatbot_variant,
        )

        # Pass the user question to the LLM chain optimized for the specific use case
        if chatbot_variant == "questionsAndAnswers":

            # Call the LLM and process the Bedrock stream of events
            ai_message = question_n_answers_chain.invoke(
                bedrock_model=bedrock_stream_model,
                message_processor=message_processor,
                chat_history=conversation,
                knowledge_base=vector_store_kb,
                stream_callback=appsync_callback_handler,
            )

        elif chatbot_variant == "rewardFunctionGeneration":

            tool_processor = ToolProcessor()

            tool_processor.register_tool(
                name="get_deepracer_track",
                description="Get information about a DeepRacer track including it´s waypoints and the coordinates for the optimal race line. (if available)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "track_name": {
                            "type": "string",
                            "description": "The name of the DeepRacer track to fetch info for",
                        }
                    },
                    "required": ["track_name"],
                },
                func=track_manager.get_track_by_name,
            )

            # Call the LLM and process the Bedrock stream of events
            ai_message = reward_function_generation_chain.invoke(
                bedrock_model=bedrock_stream_model,
                message_processor=message_processor,
                chat_history=conversation,
                tool_processor=tool_processor,
                knowledge_base=vector_store_kb,
                reward_function_examples_db=vector_store_reward_functions,
                stream_callback=appsync_callback_handler,
            )
        elif chatbot_variant == "modelEvaluation":

            # Setup the tools to make available to the LLM
            get_deepracer_model, list_deepracer_models = create_deepracer_functions(
                user_id
            )

            tool_processor = ToolProcessor()

            tool_processor.register_tool(
                name="get_deepracer_model",
                description="Fetch a DeepRacer to get the model data for analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "model_name": {
                            "type": "string",
                            "description": "The name of the DeepRacer model to fetch data for",
                        }
                    },
                    "required": ["model_name"],
                },
                func=get_deepracer_model,
            )

            tool_processor.register_tool(
                name="list_deepracer_models",
                description="Lists available models for the current user to see which models the user have access to.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                func=list_deepracer_models,
            )

            tool_processor.register_tool(
                name="get_deepracer_track",
                description="Get information about a DeepRacer track and it´s corresponding waypoints (if available)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "track_name": {
                            "type": "string",
                            "description": "The name of the DeepRacer track to fetch info for",
                        }
                    },
                    "required": ["track_name"],
                },
                func=track_manager.get_track_by_name,
            )

            # Call the LLM and process the Bedrock stream of events and tool calls (if any)
            ai_message = model_evaluation_chain.invoke(
                bedrock_model=bedrock_stream_model,
                message_processor=message_processor,
                tool_processor=tool_processor,
                chat_history=conversation,
                stream_callback=appsync_callback_handler,
            )

        else:
            return {
                "sessionId": session_id,
                "messageId": message_id,
                "status": "error",
                "errorMessage": f"Chatbot variant: {chatbot_variant} is not supported",
            }

        logger.debug(ai_message)

        # Add the final assistant message to chat history
        conversation.append(ai_message)

        # Update the chat history with the new messages to persist the conversation to be able to ask follow up questions
        chat_history.update(
            user_id=user_id, session_id=session_id, messages=conversation
        )

        # return
        return_message = {
            "sessionId": session_id,
            "messageId": message_id,
            "status": "success",
        }
        logger.info(return_message)
        return return_message

    except Exception as exception:
        logger.exception(f"An error occurred: {exception}")
        return {
            "sessionId": session_id,
            "messageId": message_id,
            "status": "error",
            "errorMessage": str(exception),
        }


def decode_content_images(content: list[dict]) -> None:
    """
    Decodes any base64 encoded images found within the content structure.

    Args:
        content (list[dict]): The content containing potential base64 encoded images.
    """
    for entry in content:
        if "image" in entry and "source" in entry["image"]:
            # Get the image bytes and decode them
            image_bytes = entry["image"]["source"]["bytes"]
            logger.info(f"image_bytes", extra={"image_bytes": image_bytes})
            decoded_bytes = safe_decode_base64(image_bytes)

            # Update the bytes section with the decoded image bytes
            logger.info(f"decoded_bytes", extra={"decoded_bytes": decoded_bytes})
            entry["image"]["source"]["bytes"] = decoded_bytes


# Initiate the tool functions with the user_id this is
# to ensure that we user id from the Cognito token and not let the LLM come up with it
def create_deepracer_functions(user_id):
    def get_deepracer_model(model_name: str) -> dict:
        model_data = model_storage.get_model(user_id, model_name)
        logger.info(
            f"model_data",
            extra={"model_data": model_data, "DDB Table": model_storage.ddbTable.name},
        )
        return model_data

    def list_deepracer_models() -> list:
        models = model_storage.list_models(user_id)
        logger.info(
            f"models",
            extra={"models": models, "DDB Table": model_storage.ddbTable.name},
        )
        return models

    return get_deepracer_model, list_deepracer_models
