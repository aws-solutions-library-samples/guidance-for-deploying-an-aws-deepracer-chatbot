from typing import Any, Dict, List
from unittest.mock import Mock

import pytest
from aws_lambda_powertools import Logger
from utils.converse_stream.tool_processor import ToolProcessor


class TestToolProcessor:

    def test_get_tools_empty_tool_specs(self):
        """
        Test get_tools when no tools have been registered.
        """
        processor = ToolProcessor()
        result = processor.get_tools()
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_tools_multiple_calls(self):
        """
        Test that multiple calls to get_tools return the same result.
        """
        processor = ToolProcessor()
        processor.register_tool(
            "test_tool",
            lambda x: x,
            "Test tool description",
            {"type": "object", "properties": {"input": {"type": "string"}}},
        )
        result1 = processor.get_tools()
        result2 = processor.get_tools()
        assert result1 == result2

    def test_get_tools_returns_registered_tool_specs(self):
        """
        Test that get_tools() returns the registered tool specifications.
        """
        # Arrange
        tool_processor = ToolProcessor()
        expected_tool_specs = [
            {
                "toolSpec": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {"input": {"type": "string"}},
                        }
                    },
                }
            }
        ]
        tool_processor.register_tool(
            name="test_tool",
            func=lambda x: x,
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {"input": {"type": "string"}},
            },
        )

        # Act
        result = tool_processor.get_tools()

        # Assert
        assert (
            result == expected_tool_specs
        ), "get_tools() should return the registered tool specifications"

    def test_get_tools_with_registered_tools(self):
        """
        Test get_tools after registering some tools.
        """
        processor = ToolProcessor()
        processor.register_tool(
            "test_tool",
            lambda x: x,
            "Test tool description",
            {"type": "object", "properties": {"input": {"type": "string"}}},
        )
        result = processor.get_tools()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["toolSpec"]["name"] == "test_tool"
        assert result[0]["toolSpec"]["description"] == "Test tool description"
        assert "inputSchema" in result[0]["toolSpec"]

    def test_handle_message_1(self):
        """
        Test handle_message when the message contains 'content' key.
        """
        # Initialize ToolProcessor
        processor = ToolProcessor()

        # Mock process_tool_requests method
        def mock_process_tool_requests(content):
            return [{"toolResult": {"status": "success"}}]

        processor.process_tool_requests = mock_process_tool_requests

        # Prepare test input
        message: Dict[str, Any] = {"content": [{"text": "Test content"}]}

        # Call the method under test
        result = processor.handle_message(message)

        # Assert the expected behavior
        assert "toolResults" in result
        assert result["toolResults"] == [{"toolResult": {"status": "success"}}]
        assert result["content"] == [{"text": "Test content"}]

    def test_handle_message_with_content(self):
        """
        Test handle_message when the message contains 'content' key.
        """
        # Initialize ToolProcessor
        processor = ToolProcessor()

        # Mock process_tool_requests method
        def mock_process_tool_requests(content):
            return [{"toolResult": {"status": "success"}}]

        processor.process_tool_requests = mock_process_tool_requests

        # Prepare test input
        message: Dict[str, Any] = {"content": [{"text": "Test content"}]}

        # Call the method under test
        result = processor.handle_message(message)

        # Assert the expected behavior
        assert "toolResults" in result
        assert result["toolResults"] == [{"toolResult": {"status": "success"}}]
        assert result["content"] == [{"text": "Test content"}]

    def test_handle_message_with_empty_content_list(self):
        """
        Test handle_message with an empty content list.
        """
        processor = ToolProcessor()
        message_with_empty_content = {"content": []}
        result = processor.handle_message(message_with_empty_content)
        assert result == {
            "content": [],
            "toolResults": [],
        }, "Expected empty toolResults for empty content"

    def test_handle_message_with_empty_input(self):
        """
        Test handle_message with an empty input dictionary.
        """
        processor = ToolProcessor()
        empty_message = {}
        result = processor.handle_message(empty_message)
        assert (
            result == {}
        ), "Expected an empty dictionary to be returned for empty input"

    def test_handle_message_with_exception_in_tool(self):
        """
        Test handle_message when a tool raises an exception.
        """

        def faulty_tool(**kwargs):
            raise ValueError("This tool always fails")

        processor = ToolProcessor()
        processor.register_tool(
            "faulty_tool", faulty_tool, "A tool that always fails", {}
        )

        message_with_faulty_tool = {
            "content": [{"toolUse": {"name": "faulty_tool", "input": {}}}]
        }
        result = processor.handle_message(message_with_faulty_tool)
        assert "toolResults" in result
        assert len(result["toolResults"]) == 1
        assert result["toolResults"][0]["toolResult"]["status"] == "error"
        assert (
            "Error: This tool always fails"
            in result["toolResults"][0]["toolResult"]["content"][0]["text"]
        )

    def test_handle_message_with_invalid_tool_use(self):
        """
        Test handle_message with invalid tool use in content.
        """
        processor = ToolProcessor()
        invalid_tool_message = {
            "content": [{"toolUse": {"name": "nonexistent_tool", "input": {}}}]
        }
        result = processor.handle_message(invalid_tool_message)
        assert "toolResults" in result
        assert len(result["toolResults"]) == 1
        assert result["toolResults"][0]["toolResult"]["status"] == "error"
        assert "Error:" in result["toolResults"][0]["toolResult"]["content"][0]["text"]

    def test_handle_message_with_missing_content(self):
        """
        Test handle_message with a message missing the 'content' key.
        """
        processor = ToolProcessor()
        message_without_content = {"someKey": "someValue"}
        result = processor.handle_message(message_without_content)
        assert result == {
            "someKey": "someValue"
        }, "Expected the input message to be returned unchanged"

    def test_handle_message_with_oversized_input(self):
        """
        Test handle_message with an oversized input that might cause memory issues.
        """
        processor = ToolProcessor()
        large_content = [{"text": "x" * 1000000}] * 1000  # 1GB of data
        large_message = {"content": large_content}

        # This test checks if the method can handle large inputs without crashing
        # It doesn't assert a specific outcome, but ensures the method completes
        result = processor.handle_message(large_message)
        assert "content" in result
        assert "toolResults" in result

    def test_handle_message_without_content(self):
        """
        Test handle_message when the message does not contain a 'content' key.
        """
        # Arrange
        tool_processor = ToolProcessor()
        message: Dict[str, Any] = {"some_key": "some_value"}

        # Act
        result = tool_processor.handle_message(message)

        # Assert
        assert result == message
        assert "toolResults" not in result

    def test_init_creates_empty_tools_and_tool_specs(self):
        """
        Test that __init__ method creates empty tools dictionary and tool_specs list.
        """
        # Arrange & Act
        processor = ToolProcessor()

        # Assert
        assert isinstance(processor.tools, dict)
        assert len(processor.tools) == 0
        assert isinstance(processor.tool_specs, list)
        assert len(processor.tool_specs) == 0

    def test_init_creates_empty_tools_and_tool_specs_2(self):
        """
        Test that __init__ creates empty tools dictionary and tool_specs list.
        """
        processor = ToolProcessor()
        assert isinstance(processor.tools, dict)
        assert len(processor.tools) == 0
        assert isinstance(processor.tool_specs, list)
        assert len(processor.tool_specs) == 0

    def test_init_creates_unique_instances(self):
        """
        Test that __init__ creates unique instances with separate tools and tool_specs.
        """
        processor1 = ToolProcessor()
        processor2 = ToolProcessor()

        processor1.tools["test"] = lambda: None
        processor1.tool_specs.append({"test": "spec"})

        assert "test" not in processor2.tools
        assert len(processor2.tool_specs) == 0

    def test_init_does_not_accept_parameters(self):
        """
        Test that __init__ raises TypeError when parameters are provided.
        """
        with pytest.raises(TypeError):
            ToolProcessor("invalid_param")

    def test_invoke_tool_exception(self):
        """
        Test invoking a tool that raises an exception.
        """
        processor = ToolProcessor()

        def error_tool():
            raise RuntimeError("Tool execution failed")

        processor.register_tool(
            name="error_tool",
            func=error_tool,
            description="A tool that always fails",
            input_schema={},
        )

        with pytest.raises(RuntimeError) as excinfo:
            processor.invoke_tool("error_tool", {})

        assert str(excinfo.value) == "Tool execution failed"

        # Check if the error was logged
        # Note: This assumes that the logger is accessible and can be checked.
        # In a real scenario, you might need to mock the logger or use a different approach to verify logging.

    def test_invoke_tool_not_found(self):
        """
        Test invoking a tool that is not registered.
        """
        processor = ToolProcessor()

        with pytest.raises(ValueError) as excinfo:
            processor.invoke_tool("non_existent_tool", {})

        assert str(excinfo.value) == "Tool not found: non_existent_tool"

    def test_invoke_tool_raises_value_error_when_tool_not_found(self):
        """
        Test that invoke_tool raises a ValueError when the tool is not found.
        """
        processor = ToolProcessor()
        non_existent_tool = "non_existent_tool"
        input_data: Dict[str, Any] = {}

        with pytest.raises(ValueError) as exc_info:
            processor.invoke_tool(non_existent_tool, input_data)

        assert str(exc_info.value) == f"Tool not found: {non_existent_tool}"

    def test_invoke_tool_success(self):
        """
        Test successful invocation of a registered tool.
        """
        # Initialize ToolProcessor
        processor = ToolProcessor()

        # Define a mock tool function
        def mock_tool(param1: str, param2: int) -> str:
            return f"Processed: {param1}, {param2}"

        # Register the mock tool
        processor.register_tool(
            name="mock_tool",
            func=mock_tool,
            description="A mock tool for testing",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
                "required": ["param1", "param2"],
            },
        )

        # Prepare input data
        input_data = {"param1": "test", "param2": 42}

        # Invoke the tool
        result = processor.invoke_tool("mock_tool", input_data)

        # Assert the result
        assert result == "Processed: test, 42"

    def test_invoke_tool_with_empty_input(self):
        """
        Test invoking a tool with empty input.
        """

        def sample_tool(**kwargs):
            if not kwargs:
                raise ValueError("Empty input")
            return "Success"

        processor = ToolProcessor()
        processor.register_tool("sample_tool", sample_tool, "Sample tool", {})

        with pytest.raises(ValueError, match="Empty input"):
            processor.invoke_tool("sample_tool", {})

    def test_invoke_tool_with_exception_in_tool(self):
        """
        Test invoking a tool that raises an exception.
        """

        def sample_tool():
            raise RuntimeError("Tool execution failed")

        processor = ToolProcessor()
        processor.register_tool("sample_tool", sample_tool, "Sample tool", {})

        with pytest.raises(RuntimeError, match="Tool execution failed"):
            processor.invoke_tool("sample_tool", {})

    def test_invoke_tool_with_invalid_input_type(self):
        """
        Test invoking a tool with invalid input type.
        """

        def sample_tool(x: int):
            return x + 1

        processor = ToolProcessor()
        processor.register_tool(
            "sample_tool", sample_tool, "Sample tool", {"x": {"type": "integer"}}
        )

        with pytest.raises(TypeError):
            processor.invoke_tool("sample_tool", {"x": "not an integer"})

    def test_invoke_tool_with_missing_required_input(self):
        """
        Test invoking a tool with missing required input.
        """

        def sample_tool(x: int, y: int):
            return x + y

        processor = ToolProcessor()
        processor.register_tool(
            "sample_tool",
            sample_tool,
            "Sample tool",
            {"x": {"type": "integer"}, "y": {"type": "integer"}},
        )

        with pytest.raises(TypeError):
            processor.invoke_tool("sample_tool", {"x": 5})

    def test_invoke_tool_with_nonexistent_tool(self):
        """
        Test invoking a tool that doesn't exist.
        """
        processor = ToolProcessor()
        with pytest.raises(ValueError, match="Tool not found: nonexistent_tool"):
            processor.invoke_tool("nonexistent_tool", {})

    def test_invoke_tool_with_out_of_bounds_input(self):
        """
        Test invoking a tool with input outside accepted bounds.
        """

        def sample_tool(x: int):
            if x < 0 or x > 100:
                raise ValueError("Input out of bounds")
            return x * 2

        processor = ToolProcessor()
        processor.register_tool(
            "sample_tool",
            sample_tool,
            "Sample tool",
            {"x": {"type": "integer", "minimum": 0, "maximum": 100}},
        )

        with pytest.raises(ValueError, match="Input out of bounds"):
            processor.invoke_tool("sample_tool", {"x": 101})

    def test_process_tool_requests_2(self):
        """
        Test process_tool_requests when 'toolUse' key is not present in any content item.
        """
        # Arrange
        tool_processor = ToolProcessor()
        message_content: List[Dict[str, Any]] = [
            {"text": "This is a test message"},
            {"image": "test_image.jpg"},
            {"audio": "test_audio.mp3"},
        ]

        # Act
        result = tool_processor.process_tool_requests(message_content)

        # Assert
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 0, "Result should be an empty list"

    def test_process_tool_requests_empty_input(self):
        """
        Test process_tool_requests with empty input.
        """
        processor = ToolProcessor()
        result = processor.process_tool_requests([])
        assert result == [], "Expected empty list for empty input"

    def test_process_tool_requests_error(self):
        """
        Test processing of tool requests when an error occurs.
        """
        # Initialize ToolProcessor
        tool_processor = ToolProcessor()

        # Mock the invoke_tool method to raise an exception
        tool_processor.invoke_tool = Mock(side_effect=Exception("Test error"))

        # Prepare test data
        message_content = [
            {
                "toolUse": {
                    "name": "test_tool",
                    "input": {"param": "value"},
                    "toolUseId": "456",
                }
            }
        ]

        # Call the method under test
        result = tool_processor.process_tool_requests(message_content)

        # Assertions
        assert len(result) == 1
        assert result[0]["toolResult"]["toolUseId"] == "456"
        assert result[0]["toolResult"]["content"][0]["text"] == "Error: Test error"
        assert result[0]["toolResult"]["status"] == "error"

        # Verify that invoke_tool was called with correct arguments
        tool_processor.invoke_tool.assert_called_once_with(
            "test_tool", {"param": "value"}
        )

    def test_process_tool_requests_invalid_input(self):
        """
        Test process_tool_requests with invalid input (no 'toolUse' key).
        """
        processor = ToolProcessor()
        invalid_input = [{"invalid_key": "value"}]
        result = processor.process_tool_requests(invalid_input)
        assert result == [], "Expected empty list for invalid input"

    def test_process_tool_requests_missing_tool_use_id(self):
        """
        Test process_tool_requests when toolUseId is missing.
        """

        def dummy_tool(**kwargs):
            return "Success"

        processor = ToolProcessor()
        processor.register_tool("dummy_tool", dummy_tool, "A dummy tool", {})

        input_data = [{"toolUse": {"name": "dummy_tool", "input": {}}}]
        result = processor.process_tool_requests(input_data)

        assert len(result) == 1
        assert result[0]["toolResult"]["toolUseId"] == ""
        assert result[0]["toolResult"]["status"] == "success"

    def test_process_tool_requests_multiple_tools(self):
        """
        Test processing of multiple tool requests.
        """
        # Initialize ToolProcessor
        tool_processor = ToolProcessor()

        # Mock the invoke_tool method
        tool_processor.invoke_tool = Mock(side_effect=["Result 1", "Result 2"])

        # Prepare test data
        message_content = [
            {
                "toolUse": {
                    "name": "tool1",
                    "input": {"param1": "value1"},
                    "toolUseId": "789",
                }
            },
            {
                "toolUse": {
                    "name": "tool2",
                    "input": {"param2": "value2"},
                    "toolUseId": "101112",
                }
            },
        ]

        # Call the method under test
        result = tool_processor.process_tool_requests(message_content)

        # Assertions
        assert len(result) == 2
        assert result[0]["toolResult"]["toolUseId"] == "789"
        assert result[0]["toolResult"]["content"][0]["text"] == "Result 1"
        assert result[0]["toolResult"]["status"] == "success"
        assert result[1]["toolResult"]["toolUseId"] == "101112"
        assert result[1]["toolResult"]["content"][0]["text"] == "Result 2"
        assert result[1]["toolResult"]["status"] == "success"

        # Verify that invoke_tool was called with correct arguments
        tool_processor.invoke_tool.assert_any_call("tool1", {"param1": "value1"})
        tool_processor.invoke_tool.assert_any_call("tool2", {"param2": "value2"})

    def test_process_tool_requests_multiple_tools_2(self):
        """
        Test process_tool_requests with multiple tool requests, including a mix of successful and failing tools.
        """

        def success_tool(**kwargs):
            return "Success"

        def failing_tool(**kwargs):
            raise ValueError("Tool execution failed")

        processor = ToolProcessor()
        processor.register_tool("success_tool", success_tool, "A successful tool", {})
        processor.register_tool("failing_tool", failing_tool, "A failing tool", {})

        input_data = [
            {"toolUse": {"name": "success_tool", "input": {}, "toolUseId": "1"}},
            {"toolUse": {"name": "failing_tool", "input": {}, "toolUseId": "2"}},
            {"toolUse": {"name": "non_existent_tool", "input": {}, "toolUseId": "3"}},
        ]

        result = processor.process_tool_requests(input_data)

        assert len(result) == 3
        assert result[0]["toolResult"]["status"] == "success"
        assert result[0]["toolResult"]["toolUseId"] == "1"
        assert result[1]["toolResult"]["status"] == "error"
        assert result[1]["toolResult"]["toolUseId"] == "2"
        assert result[2]["toolResult"]["status"] == "error"
        assert result[2]["toolResult"]["toolUseId"] == "3"

    def test_process_tool_requests_no_tool_use(self):
        """
        Test process_tool_requests when no 'toolUse' key is present in the message content.
        """
        # Arrange
        tool_processor = ToolProcessor()
        message_content = [{"text": "Hello, world!"}, {"image": "image_url.jpg"}]

        # Act
        result = tool_processor.process_tool_requests(message_content)

        # Assert
        assert result == [], "Expected an empty list when no 'toolUse' is present"

    def test_process_tool_requests_no_tool_use_2(self):
        """
        Test processing of message content without tool use.
        """
        # Initialize ToolProcessor
        tool_processor = ToolProcessor()

        # Prepare test data
        message_content = [{"text": "This is a message without tool use"}]

        # Call the method under test
        result = tool_processor.process_tool_requests(message_content)

        # Assertions
        assert len(result) == 0

    def test_process_tool_requests_success(self):
        """
        Test successful processing of tool requests.
        """
        # Initialize ToolProcessor
        tool_processor = ToolProcessor()

        # Mock the invoke_tool method
        tool_processor.invoke_tool = Mock(return_value="Tool result")

        # Prepare test data
        message_content = [
            {
                "toolUse": {
                    "name": "test_tool",
                    "input": {"param": "value"},
                    "toolUseId": "123",
                }
            }
        ]

        # Call the method under test
        result = tool_processor.process_tool_requests(message_content)

        # Assertions
        assert len(result) == 1
        assert result[0]["toolResult"]["toolUseId"] == "123"
        assert result[0]["toolResult"]["content"][0]["text"] == "Tool result"
        assert result[0]["toolResult"]["status"] == "success"

        # Verify that invoke_tool was called with correct arguments
        tool_processor.invoke_tool.assert_called_once_with(
            "test_tool", {"param": "value"}
        )

    def test_process_tool_requests_tool_execution_error(self):
        """
        Test process_tool_requests when tool execution raises an exception.
        """

        def failing_tool(**kwargs):
            raise ValueError("Tool execution failed")

        processor = ToolProcessor()
        processor.register_tool(
            "failing_tool", failing_tool, "A tool that always fails", {}
        )

        input_data = [{"toolUse": {"name": "failing_tool", "input": {}}}]
        result = processor.process_tool_requests(input_data)

        assert len(result) == 1
        assert result[0]["toolResult"]["status"] == "error"
        assert "Tool execution failed" in result[0]["toolResult"]["content"][0]["text"]

    def test_process_tool_requests_tool_not_found(self):
        """
        Test process_tool_requests with a non-existent tool.
        """
        processor = ToolProcessor()
        input_data = [{"toolUse": {"name": "non_existent_tool", "input": {}}}]
        result = processor.process_tool_requests(input_data)
        assert len(result) == 1
        assert result[0]["toolResult"]["status"] == "error"
        assert "Tool not found" in result[0]["toolResult"]["content"][0]["text"]

    def test_register_tool_successfully(self):
        """
        Test that a tool is successfully registered with the ToolProcessor.
        """
        # Arrange
        processor = ToolProcessor()
        name = "test_tool"

        def dummy_func():
            pass

        description = "A test tool"
        input_schema = {"type": "object", "properties": {"input": {"type": "string"}}}

        # Act
        processor.register_tool(name, dummy_func, description, input_schema)

        # Assert
        assert name in processor.tools
        assert processor.tools[name] == dummy_func
        assert len(processor.tool_specs) == 1
        assert processor.tool_specs[0] == {
            "toolSpec": {
                "name": name,
                "description": description,
                "inputSchema": {"json": input_schema},
            }
        }
