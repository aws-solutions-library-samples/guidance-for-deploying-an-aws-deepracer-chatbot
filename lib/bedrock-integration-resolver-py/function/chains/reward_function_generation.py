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

system_prompt = """You are an expert AI assistant with in-depth knowledge of AWS DeepRacer, specializing in generating reward functions for DeepRacer models. Your primary task is to help users generate, analyze, and modify reward functions for given AWS DeepRacer tracks.

You will receive from the user:
- <input> User's question (mandatory)

Other artifacts that might be added from the RAG pipeline:
- <context> Additional context about AWS DeepRacer from reliable sources, DeepRacer documentation, FAQ, track layouts and track info (optional)
- <examples> Related Reward function examples (optional)

Always focus on the mandatory user input as your primary goal. Use any provided optional information to generate an appropriate output.

<guidelines_and_constraints>
- Provide clear, easy-to-follow next steps for the user.
- Ensure all analysis and Python functions can be performed solely within the AWS DeepRacer console.
- Do not reference or recommend external tools, data sources, or actions outside the AWS DeepRacer environment.
- Combine multiple reward components (e.g., speed, distance from center, progress) into a final reward.
- Include progress-based rewards to encourage completing laps quickly.
- Avoid hard-coding specific track information to allow for better generalization.
- Normalize and combine reward components with tunable weights.
- Always return positive float values, even for suboptimal actions (minimum 1e-3).
- Use exponential functions for reward scaling to create stronger gradients for desired behaviors.
- Reward alignment between the car's heading and the track direction.
- Properly penalize off-track behavior without using zero rewards.
- Consider the chosen action space when designing the reward function, adhering to these constraints:
    - Steering angle range: Left turn (0 to 30 degrees), Right turn (-30 to 0 degrees)
    - Speed range: Minimum (0.1 to 4 m/s), Maximum (0.1 to 4 m/s)
- Keep the reward function computationally efficient by limiting complex mathematical operations.
- Use only the provided input parameters in the reward function.
- Keep the reward function size within AWS DeepRacer's limits.


<output_process>
- Analyze the given information and plan how to generate a reward function that fits the user's criteria. Include your reasoning for parameter values in the "thought" element.
- Generate the reward function in Python using Markdown format. Output this in the "answer" element.
- Provide a concise explanation of the new or improved reward function, suitable for beginners, in the "explanation" element.

<output_format>
Always follow this VALID JSON output format:
{
"thought": "Your analysis and reasoning",
"answer": "Generated reward function in Python (Markdown format)",
"explanation": "Beginner-friendly explanation of the function"
}
</output_format>
"""


def invoke(
    bedrock_model: BedrockStream,
    message_processor: MessageProcessor,
    chat_history: List[Dict[str, str]],
    knowledge_base: Callable = None,
    reward_function_examples_db: Callable = None,
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

    # Isolate the chat_history to only have the user message and the final assistant message stored
    isolated_chat_history = copy.copy(chat_history)

    # Get the content from last user message in the chat history
    # we want to use that for doing the similarity search in the knowledge base
    user_message = isolated_chat_history[-1]
    content = user_message.get("content")

    # The Embedding model use the Bedrock invoke API, so we need to convert the content from converse API format to the bedrock invoke API format
    bedrock_invoke_formatted_content = from_bedrock_converse_to_bedrock_invoke(content)
    print("\n Bedrock Invoke formatted content:")
    print(bedrock_invoke_formatted_content)

    # Perform similarity search and retrieve the top 3 similar documents and images
    rag_content = knowledge_base.similarity_search(
        query=bedrock_invoke_formatted_content, k=3
    )

    # Convert the knowledge base output into Bedrock converse message format
    results = to_converse_api_content(query_results=rag_content)
    print("\nReturned documents from the knowledge base:")
    pprint(results)

    # Retrieve the reward function examples relevant for answering the users query
    reward_function_examples = reward_function_examples_db.similarity_search(
        query=bedrock_invoke_formatted_content, k=3
    )

    reward_function_examples_as_content = to_converse_api_content(
        query_results=reward_function_examples, content_type="examples"
    )
    print("\nReturned reward function examples from the knowledge base:")
    pprint(reward_function_examples_as_content)

    # Extend the content with the RAG results to maintain a flat structure
    user_message["content"].extend(results)
    user_message["content"].extend(reward_function_examples_as_content)
    print("\n User message with appended RAG content & reward function examples:")
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
