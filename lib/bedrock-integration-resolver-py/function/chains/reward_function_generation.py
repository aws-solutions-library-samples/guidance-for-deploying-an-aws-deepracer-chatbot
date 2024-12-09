import copy
from typing import Any, Callable, Dict, List

from aws_lambda_powertools import Logger
from knowledge_base.output_converters import content_to_string, to_converse_api_content
from utils.converse_stream import (
    BedrockStream,
    MessageProcessor,
    ToolProcessor,
    from_bedrock_converse_to_bedrock_invoke,
)

logger = Logger()

base_system_prompt = """
You are an AI assistant specializing in AWS DeepRacer, with a focus on generating and analyzing reward functions for DeepRacer models. Your primary task is to assist users in creating, modifying, and optimizing reward functions for various AWS DeepRacer tracks.

Please format your entire response using Markdown syntax, following these guidelines:
1. Use standard Markdown for text formatting
2. For Python code blocks, use triple backticks with the language specified:

   ```python
   def example_function():
       return "This is a Python function"
3. Ensure that any Python code have 2 spaces of indentation

Input Format:
- User's question about DeepRacer reward functions


Here is additional relevant DeepRacer information:
<context></context>

Here are relevant examples of reward functions:
<examples></examples>

Guidelines for Reward Function Development:

1. Reward Function Composition:
   - If the <input> do not mention waypoints or optimal race line, avoid generating waypoint based reward functions.
   - Combine multiple reward components (e.g., speed, distance from center, progress).
   - Include progress-based rewards to encourage completing laps quickly.
   - Avoid hard-coding specific track information for better generalization.
   - Normalize and combine reward components with tunable weights.
   - Always return positive float values (minimum 1e-3), even for suboptimal actions.
   - Use exponential functions for reward scaling to create stronger gradients.
   - Reward alignment between the car's heading and the track direction.
   - Properly penalize off-track behavior without using zero rewards.

2. Technical Constraints:
   - Ensure all Python functions can be executed within the AWS DeepRacer console.
   - Adhere to the action space constraints:
     * Steering angle range: Left turn (0 to 30 degrees), Right turn (-30 to 0 degrees)
     * Speed range: Minimum (0.1 to 4 m/s), Maximum (0.1 to 4 m/s)
   - Use a discount factor hyper-parameter value of 0.95.
   - Keep reward functions computationally efficient.
   - Place any Python module imports at the top of the file.

3. Track-Specific Considerations:
   - If no track name is provided, assume it is the re:Invent 2018 track.
   - When adding optimal racing line coordinates, provide all coordinates to ensure the output is valid Python code.

4. Analysis and Optimization:
   - Study correlations between specific driving behaviors and rewards.
   - Ensure desired behaviors are consistently and appropriately rewarded.
   - Provide clear, easy-to-follow next steps for optimizing reward functions.

5. Versioning:
   - If you encounter potential discrepancies between your knowledge and current AWS DeepRacer features, acknowledge this possibility to the user.
   - Encourage users to verify information with the latest AWS DeepRacer documentation.

Response Format:
- If the user question is unrelated to DeepRacer reward functions polity remind them about what you can support them on.

1. Begin with a brief summary of how you plan to address the user's reward function query.
2. Provide an explanation or analysis of the reward function, using markdown for formatting.
3. Include Python code in code blocks when generating or modifying reward functions.
4. Conclude with clear next steps or recommendations for optimizing the reward function.

Remember, your primary goal is to assist users in creating effective and efficient reward functions for AWS DeepRacer, ensuring they adhere to best practices and technical constraints.
"""


def update_system_prompt(system_prompt, new_examples=None, new_context=None):
    """
    Update the system prompt string with new examples and/or context.

    Args:
    system_prompt (str): The original system prompt string.
    new_examples (list, optional): A list of strings, each containing a new example.
    new_context (str, optional): A string containing new context information.

    Returns:
    str: The updated system prompt string with new examples and/or context added.
    """

    def update_section(prompt, section_name, new_content):
        start_tag = f"<{section_name}>"
        end_tag = f"</{section_name}>"
        start = prompt.find(start_tag)
        end = prompt.find(end_tag)

        if start == -1 or end == -1:
            raise ValueError(
                f"Could not find the <{section_name}> tags in the system prompt."
            )

        existing_content = prompt[start + len(start_tag) : end].strip()

        if isinstance(new_content, list):
            updated_content = existing_content + "\n\n" + "\n\n".join(new_content)
        else:
            updated_content = existing_content + "\n\n" + new_content

        return (
            prompt[: start + len(start_tag)]
            + "\n"
            + updated_content
            + "\n"
            + prompt[end:]
        )

    updated_prompt = system_prompt
    try:
        if new_examples:
            logger.info(
                "Adding new examples to system prompt",
                extra={"new_examples": new_examples},
            )
            updated_prompt = update_section(updated_prompt, "examples", new_examples)

        if new_context:
            logger.info(
                "Adding new context to system prompt",
                extra={"new_context": new_context},
            )
            updated_prompt = update_section(updated_prompt, "context", new_context)
    except Exception as e:
        logger.error(f"Failed to update system prompt: {e}")
    logger.info("Updated system prompt:", extra={"updated_prompt": updated_prompt})
    return updated_prompt


def invoke(
    bedrock_model: BedrockStream,
    message_processor: MessageProcessor,
    chat_history: List[Dict[str, str]],
    tool_processor: ToolProcessor,
    knowledge_base: Callable = None,
    reward_function_examples_db: Callable = None,
    stream_callback: Callable[[str], None] = None,
    max_tool_iterations: int = 3,  # Add a maximum number of iterations
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
    logger.info(
        "Bedrock Invoke formatted content:",
        extra={"bedrock_invoke_formatted_content": bedrock_invoke_formatted_content},
    )

    # Retrieve the reward function examples relevant for answering the users query
    reward_function_examples = reward_function_examples_db.similarity_search(
        query=bedrock_invoke_formatted_content, k=3
    )
    system_prompt = update_system_prompt(
        system_prompt=base_system_prompt,
        new_examples=content_to_string(reward_function_examples),
    )

    final_assistant_message = None
    try:
        for _ in range(max_tool_iterations):

            stream = bedrock_model(
                messages=isolated_chat_history,
                system_prompt=system_prompt,
                tool_list=tool_processor.get_tools(),
            )

            assistant_message = message_processor.process_stream(
                events=stream, stream_callback=stream_callback
            )
            logger.info(
                f"Assistant message:", extra={"assistant_message": assistant_message}
            )
            isolated_chat_history.append(assistant_message)

            tool_results = tool_processor.process_tool_requests(
                assistant_message["content"]
            )

            if tool_results:
                user_message = {"role": "user", "content": tool_results}
                logger.info(f"Tool results:", extra={"tool_results": tool_results})
                isolated_chat_history.append(user_message)
            else:
                logger.info(
                    f"No tools to process, finishing...",
                    extra={"final_assistant_message": assistant_message},
                )
                final_assistant_message = assistant_message
                break

        if final_assistant_message is None:
            logger.error(f"Reached maximum iterations without completion.")
            final_assistant_message = assistant_message

        return final_assistant_message

    except Exception as e:
        logger.exception(f"Error in model evaluation: {e}")
        raise
