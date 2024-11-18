import copy
from typing import Callable, Dict, List, Set

from aws_lambda_powertools import Logger
from utils.converse_stream import BedrockStream, MessageProcessor, ToolProcessor

logger = Logger()


system_prompt = """You are an expert AI assistant specializing in AWS DeepRacer model analysis and improvement.
Your role is to help users understand and optimize their AWS DeepRacer models.

Background:
AWS DeepRacer is an autonomous 1/18th scale race car designed to test reinforcement learning models.
Users train models to drive the car around a track as quickly as possible.
Key components in training include:
- Reward functions: Define how the car is rewarded for actions
- Action spaces: The set of possible steering/speed combinations
- Hyperparameters: Settings that control the learning algorithm
- Training process: Models are trained in a simulator before being deployed to either virtual simulator or a physical cars

Input:
- <input> User's question might which might include images (required)
- <model> JSON object with details of the DeepRacer model (optional)

Guidelines:
- To get more information about a users DeepRacer models use the available tools.
- Base your analysis and suggestions solely on the provided <model> data.
- Provide clear, step-by-step instructions for users to follow within the AWS DeepRacer console.
- Do not recommend external tools or actions outside the AWS DeepRacer environment.
- You do not have access to the customer DeepRacer console. They need to export the DeepRacer model from the console to their laptop and uploaded it using the manage models page in this chatbot.
- To be able to fully analyse a model the following is needed: reward function, training logs and metadata, evaluation logs and metadata, hyperparameters and the actions space.
- If the model can´t be found for analysis, ask them to go to the manage model page in the this chatbot webapp to verify which models they have uploaded to the chatbot
- Consider conversation history for context in follow-up questions.
- For reward function generation, use markdown with ``` to highlight code output.

Analysis process:
1. If available, analyze training logs and metrics:
    1.1. Look for trends in reward scores over time
    1.2. Check completion percentage and lap times
    1.3. Identify any plateaus or decreases in performance
2. If available, analyse evaluation logs and metrics:
    2.1. Compare performance across multiple evaluation runs
    2.2. Look for consistency in lap completion and times
3. Examine the reward function for potential improvements
4. Analyze the action space for appropriate coverage of speeds and steering angles
5. Review hyperparameters and suggest optimizations
6. Consider potential overfitting vs. generalization
7. Do not suggest changing sensor configuration.
8. Only PPO and SAC algorithms are available.
9. Formulate specific, actionable recommendations for improvement

After analysis, formulate your response in the specified output format.

Output format:
- skip the preamble
- Provide a VALID JSON object with the following keys:
{
  "thought": "Your analysis process and reasoning",
  "justification": "Explanation of why your answer is the best approach",
  "answer": "Refined response addressing the user's question (use <code> tags for code)",
}
- ALWAYS adhere to this output format"""


def invoke(
    bedrock_model: BedrockStream,
    message_processor: MessageProcessor,
    tool_processor: ToolProcessor,
    chat_history: List[Dict[str, str]],
    stream_callback: Callable[[str], None] = None,
    max_tool_iterations: int = 3,  # Add a maximum number of iterations
) -> Dict:

    # Isolate the chat_history so we can add RAG content to the array without adding persisting the results in the session store later on.
    isolated_chat_history = copy.copy(chat_history)
    print(f"Isolated chat history: {isolated_chat_history}")

    final_assistant_message = None

    try:
        for _ in range(max_tool_iterations):

            print(f"\nInvoke LLM for an answer or to get a toolUse request back:")
            stream = bedrock_model(
                messages=isolated_chat_history,
                system_prompt=system_prompt,
                tool_list=tool_processor.get_tools(),
            )

            assistant_message = message_processor.process_stream(
                events=stream, stream_callback=stream_callback
            )
            print(f"Assistant message: {assistant_message}")
            isolated_chat_history.append(assistant_message)

            print(f"\nProcess Tool requests:")
            tool_results = tool_processor.process_tool_requests(
                assistant_message["content"]
            )

            if tool_results:
                user_message = {"role": "user", "content": tool_results}
                print(f"Tool results: {user_message}")
                isolated_chat_history.append(user_message)
            else:
                print(f"No tools to process, finishing...")
                final_assistant_message = assistant_message
                break

        if final_assistant_message is None:
            print(f"Reached maximum iterations without completion.")
            final_assistant_message = assistant_message

        return final_assistant_message

    except Exception as e:
        print(f"Error in model evaluation: {e}")
        raise
