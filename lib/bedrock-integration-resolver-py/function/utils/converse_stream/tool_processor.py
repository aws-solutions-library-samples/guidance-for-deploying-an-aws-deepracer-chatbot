from typing import Any, Callable, Dict, List, Optional

from aws_lambda_powertools import Logger

logger = Logger()


class ToolProcessor:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_specs: List[Dict[str, Any]] = []

    def register_tool(
        self, name: str, func: Callable, description: str, input_schema: Dict[str, Any]
    ) -> None:
        """
        Register a tool with the processor and add its configuration.

        Args:
            name (str): The name of the tool.
            func (Callable): The function to be called when the tool is invoked.
            description (str): A description of the tool.
            input_schema (Dict[str, Any]): The JSON schema for the tool's input.
        """
        self.tools[name] = func
        self.tool_specs.append(
            {
                "toolSpec": {
                    "name": name,
                    "description": description,
                    "inputSchema": {"json": input_schema},
                }
            }
        )
        logger.info(f"Registered tool: {name}")
        print(f"Registered tools: {self.tool_specs}")

    def invoke_tool(self, name: str, input_data: Dict[str, Any]) -> Any:
        """
        Invoke a registered tool.

        Args:
            name (str): The name of the tool to invoke.
            input_data (Dict[str, Any]): The input data for the tool.

        Returns:
            Any: The result of the tool invocation.

        Raises:
            ValueError: If the tool is not found.
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        try:
            result = self.tools[name](**input_data)
            return result
        except Exception as e:
            logger.error(f"Error invoking tool {name}: {str(e)}")
            raise

    def process_tool_requests(
        self, message_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process tool requests from the message content.

        Args:
            message_content (List[Dict[str, Any]]): The content of the message containing tool requests.

        Returns:
            List[Dict[str, Any]]: A list of tool results.
        """
        tool_results = []
        for content in message_content:
            if "toolUse" in content:
                tool_use = content["toolUse"]
                try:
                    result = self.invoke_tool(tool_use["name"], tool_use["input"])
                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use.get("toolUseId", ""),
                                "content": [{"text": str(result)}],
                                "status": "success",
                            }
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing tool request: {str(e)}")
                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use.get("toolUseId", ""),
                                "content": [{"text": f"Error: {str(e)}"}],
                                "status": "error",
                            }
                        }
                    )
        return tool_results

    def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a complete message and process any tool requests.

        Args:
            message (Dict[str, Any]): The complete message from the model.

        Returns:
            Dict[str, Any]: The message with added tool results.
        """
        if "content" in message:
            tool_results = self.process_tool_requests(message["content"])
            message["toolResults"] = tool_results
        return message

    def get_tools(self) -> Dict[str, Any]:
        """
        Get the registered tool specs for use with the Bedrock Stream Class.

        Returns:
            Dict[str, Any]: The tool configuration.
        """
        return self.tool_specs
