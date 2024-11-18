import copy
from pprint import pprint
from typing import Any, Callable, Dict, List

from aws_lambda_powertools import Logger
from knowledge_base.output_converters import to_converse_api_content
from utils.converse_stream import (
    BedrockStream,
    MessageProcessor,
    from_bedrock_converse_to_bedrock_invoke,
)

logger = Logger()

system_prompt = """You are an expert AI assistant specializing in AWS DeepRacer. Your task is to help users improve their knowledge of AWS DeepRacer and its capabilities, providing information and suggestions that can be implemented solely within the AWS DeepRacer Console.

You will receive from the user:
- <input> User's question (mandatory)

Other artifacts that might be added from the RAG pipeline:
- Do not explicitly mention the context or examples if they are not provided.
- <context> (optional) Additional context about AWS DeepRacer from reliable sources, DeepRacer documentation, FAQ, track layouts and track info.
- <examples> (optional) Related AWS DeepRacer examples

Analyze all provided information carefully, focusing primarily on addressing the user's question from <input>.

<guidelines>
- First, analyze the information and plan your approach. Include your reasoning in the "thought" element.
- If you lack sufficient information to answer, politely suggest consulting AWS DeepRacer documentation.
- Support your answer with relevant details from the context without explicitly mentioning the context.
- Consider conversation history for context in follow-up questions.
- Provide clear, easy-to-follow next steps for the user.
- Ensure all suggestions can be performed within the AWS DeepRacer console.
- Do not recommend external tools, data sources, or actions outside the AWS DeepRacer environment.

- Use simple language suitable for beginners in your explanation.
</guidelines>

<output_format>
Always follow this VALID JSON output format:
{
  "thought": "Your analysis and reasoning",
  "answer": "Your response to the user's question",
  "explanation": "Beginner-friendly explanation of your answer"
}

- ALWAYS adhere to this output format
</output_format>"""


def invoke(
    bedrock_model: BedrockStream,
    message_processor: MessageProcessor,
    chat_history: List[Dict[str, str]],
    knowledge_base: Callable = None,
    stream_callback: Callable[[str], None] = None,
) -> dict:
    """
    Handle the questions and answers flow.

    Args:
        bedrock_model (BedrockStream): The streaming Bedrock chat model function.
        message_processor: (MessageProcessor): The processor to use for processing the Bedrock stream of events.
        chat_history (list): All user and assistant messages to pass to the LLM
        stream_callback (Callable): Function to which the generated text should be streamed.

    Returns:
        dict: The final answer from the LLM on the users question.
    """

    # Isolate the chat_history so we can add RAG content to the array without adding persisting the results in the session store later on.
    isolated_chat_history = copy.copy(chat_history)

    # Get the content from last user message in the chat history
    # we want to use that for doing the similarity search in the knowledge base
    user_message = isolated_chat_history[-1]
    content = user_message.get("content")

    # The Embedding model use the Bedrock invoke API, so we need to convert the content from converse API format to the bedrock invoke API format
    bedrock_invoke_formatted_content = from_bedrock_converse_to_bedrock_invoke(content)

    # Perform similarity search and retrieve the top 3 results
    rag_content = knowledge_base.similarity_search(
        query=bedrock_invoke_formatted_content, k=3
    )

    # Convert the knowledge base output into Bedrock converse message format
    results = to_converse_api_content(rag_content)
    print("\nReturned documents from the knowledge base:")
    pprint(results)

    # Extend the content with the RAG results to maintain a flat structure
    user_message["content"].extend(results)
    print("\n User message with appended RAG content:")
    pprint(user_message)
    isolated_chat_history[-1] = user_message

    print("\n Messages to send to Bedrock, which will be passed to the LLM:")
    pprint(isolated_chat_history)

    # Invoke LLM model to start the completion stream
    stream = bedrock_model(messages=isolated_chat_history, system_prompt=system_prompt)

    # Process the Bedrock event stream and stream the text output to the stream_callback function
    print("\n Streaming responses from Bedrock:")
    assistant_message = message_processor.process_stream(stream, stream_callback)

    # Return the final assistant message
    return assistant_message
