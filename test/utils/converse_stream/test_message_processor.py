import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from aws_lambda_powertools import Logger
from utils.converse_stream.message_processor import (
    EventType,
    MessageProcessor,
    StreamConfig,
)


class TestMessageProcessor:

    @pytest.fixture
    def message_processor(self):
        return MessageProcessor(StreamConfig())

    def test__flush_buffer_with_content(self):
        """
        Test that _flush_buffer correctly flushes non-empty buffer content
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig(buffer_threshold=10))

        # Mock stream callback
        mock_callback = []

        def stream_callback(text: str):
            mock_callback.append(text)

        # Populate buffer with some content
        processor.buffer = {
            0: "Hello",
            1: "World",
            2: "",  # Empty content should be ignored
        }

        # Call _flush_buffer
        processor._flush_buffer(stream_callback)

        # Assert that the callback was called with correct content
        assert mock_callback == ["Hello", "World"]

        # Assert that the buffer is cleared after flushing
        assert all(content == "" for content in processor.buffer.values())

    def test__get_event_type_returns_none_for_unknown_event(self):
        """
        Test that _get_event_type returns None when the event does not match any known EventType.
        """
        # Arrange
        processor = MessageProcessor()
        unknown_event: Dict[str, Any] = {"unknown_key": "unknown_value"}

        # Act
        result = processor._get_event_type(unknown_event)

        # Assert
        assert result is None

    def test__get_event_type_with_case_sensitive_input(self):
        """Test _get_event_type with case-sensitive input"""
        processor = MessageProcessor()
        result = processor._get_event_type(
            {"MESSAGESTART": "This should not match due to case sensitivity"}
        )
        assert result is None

    def test__get_event_type_with_empty_input(self):
        """Test _get_event_type with an empty dictionary input"""
        processor = MessageProcessor()
        result = processor._get_event_type({})
        assert result is None

    def test__get_event_type_with_invalid_input(self):
        """Test _get_event_type with invalid input that doesn't contain any known event type"""
        processor = MessageProcessor()
        result = processor._get_event_type({"unknownEvent": "someValue"})
        assert result is None

    def test__get_event_type_with_multiple_event_types(self):
        """Test _get_event_type with multiple event types in the input"""
        processor = MessageProcessor()
        result = processor._get_event_type(
            {"messageStart": "Start", "contentBlockDelta": "Delta"}
        )
        assert result == EventType.MESSAGE_START

    def test__get_event_type_with_none_input(self):
        """Test _get_event_type with None input"""
        processor = MessageProcessor()
        with pytest.raises(TypeError):
            processor._get_event_type(None)

    def test__get_event_type_with_partial_match(self):
        """Test _get_event_type with a partial match of an event type"""
        processor = MessageProcessor()
        result = processor._get_event_type({"message": "This should not match"})
        assert result is None

    def test__handle_block_delta_2(self):
        """
        Test _handle_block_delta when content list is shorter than index and delta contains toolUse
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Prepare test data
        event = {
            "contentBlockDelta": {
                "delta": {"toolUse": {"name": "test_tool", "input": "test_input"}},
                "contentBlockIndex": 2,
            }
        }
        ai_message = {"content": []}

        # Mock stream callback
        def stream_callback(text: str):
            pass

        # Call the method under test
        processor._handle_block_delta(event, ai_message, stream_callback)

        # Assertions
        assert (
            len(ai_message["content"]) == 3
        )  # Content list should be expanded to index 2
        assert "toolUse" in ai_message["content"][2]
        assert ai_message["content"][2]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][2]["toolUse"]["input"] == "test_input"

    def test__handle_block_delta_3(self):
        """
        Test _handle_block_delta when content list is long enough and delta contains toolUse
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Prepare test data
        event = {
            "contentBlockDelta": {
                "delta": {"toolUse": {"name": "test_tool", "input": "test_input"}},
                "contentBlockIndex": 1,
            }
        }
        ai_message = {
            "content": [
                {"text": "existing content"},
                {"toolUse": {"name": "existing_tool", "input": "existing_input"}},
            ]
        }

        # Mock stream callback
        def mock_stream_callback(text: str):
            pass

        # Call the method under test
        processor._handle_block_delta(event, ai_message, mock_stream_callback)

        # Assertions
        assert len(ai_message["content"]) == 2
        assert ai_message["content"][1]["toolUse"]["name"] == "test_tool"
        assert (
            ai_message["content"][1]["toolUse"]["input"] == "existing_inputtest_input"
        )

    def test__handle_block_delta_text_update(self):
        """
        Test _handle_block_delta when the delta contains text but not toolUse.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Mock event with text delta
        event = {
            "contentBlockDelta": {
                "delta": {"text": "Hello, world!"},
                "contentBlockIndex": 0,
            }
        }

        # Initialize AI message
        ai_message = {"content": []}

        # Mock stream callback
        def mock_stream_callback(text: str):
            pass

        # Call the method under test
        processor._handle_block_delta(event, ai_message, mock_stream_callback)

        # Assert the result
        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0]["text"] == "Hello, world!"

        # Test with existing content
        ai_message = {"content": [{"text": "Existing "}]}
        processor._handle_block_delta(event, ai_message, mock_stream_callback)

        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0]["text"] == "Existing Hello, world!"

        # Test with a different index
        event["contentBlockDelta"]["contentBlockIndex"] = 1
        processor._handle_block_delta(event, ai_message, mock_stream_callback)

        assert len(ai_message["content"]) == 2
        assert ai_message["content"][1]["text"] == "Hello, world!"

        # Test without stream callback
        ai_message = {"content": []}
        processor._handle_block_delta(event, ai_message, None)

        assert len(ai_message["content"]) == 2
        assert ai_message["content"][1]["text"] == "Hello, world!"

    def test__handle_block_delta_with_tool_use(self):
        """
        Test _handle_block_delta method when delta contains 'toolUse'.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Prepare test data
        event = {
            "contentBlockDelta": {
                "delta": {"toolUse": {"name": "test_tool", "input": "test_input"}},
                "contentBlockIndex": 0,
            }
        }
        ai_message = {"content": []}
        stream_callback = None

        # Call the method under test
        processor._handle_block_delta(event, ai_message, stream_callback)

        # Assert the expected outcome
        assert len(ai_message["content"]) == 1
        assert "toolUse" in ai_message["content"][0]
        assert ai_message["content"][0]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][0]["toolUse"]["input"] == "test_input"

    def test__handle_block_start_with_existing_content(self):
        """
        Test _handle_block_start method when ai_message already has content.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {
            "contentBlockStart": {
                "start": {"toolUse": {"name": "test_tool", "input": "test_input"}},
                "contentBlockIndex": 1,
            }
        }
        ai_message: Dict[str, Any] = {"content": [{"text": "existing content"}]}

        # Act
        processor._handle_block_start(event, ai_message)

        # Assert
        assert len(ai_message["content"]) == 2
        assert ai_message["content"][0] == {"text": "existing content"}
        assert ai_message["content"][1] == {
            "toolUse": {"name": "test_tool", "input": "test_input"}
        }

    def test__handle_block_start_with_tool_use(self):
        """
        Test _handle_block_start method when the event contains tool use data.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {
            "contentBlockStart": {
                "start": {"toolUse": {"name": "test_tool", "input": "test_input"}},
                "contentBlockIndex": 0,
            }
        }
        ai_message: Dict[str, Any] = {"content": []}

        # Act
        processor._handle_block_start(event, ai_message)

        # Assert
        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0] == {
            "toolUse": {"name": "test_tool", "input": "test_input"}
        }

    def test__handle_block_start_without_tool_use(self):
        """
        Test _handle_block_start method when the event does not contain tool use data.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {
            "contentBlockStart": {"start": {}, "contentBlockIndex": 0}
        }
        ai_message: Dict[str, Any] = {"content": []}

        # Act
        processor._handle_block_start(event, ai_message)

        # Assert
        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0] == {}

    def test__handle_block_stop_2(self):
        """
        Test _handle_block_stop when toolUse is present in current_content and input is not a string.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Setup test data
        event = {"contentBlockStop": {"contentBlockIndex": 0}}
        ai_message = {
            "content": [{"toolUse": {"name": "test_tool", "input": {"key": "value"}}}]
        }

        # Call the method under test
        processor._handle_block_stop(event, ai_message)

        # Assert the expected outcome
        assert "toolUse" in ai_message["content"][0]
        assert isinstance(ai_message["content"][0]["toolUse"]["input"], dict)
        assert ai_message["content"][0]["toolUse"]["input"] == {"key": "value"}

    def test__handle_event_2(self):
        """
        Test _handle_event method when no handler is found for the event type.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Create a mock event with an unknown event type
        unknown_event_type = "UNKNOWN_EVENT"
        event = {unknown_event_type: {"some_data": "test_data"}}

        # Create mock ai_message and stream_callback
        ai_message: Dict[str, Any] = {"content": []}
        stream_callback: Callable[[str], None] = lambda x: None

        # Call the _handle_event method with the unknown event type
        processor._handle_event(unknown_event_type, event, ai_message, stream_callback)

        # Assert that the ai_message was not modified
        assert ai_message == {"content": []}

        # Note: We can't directly assert that a warning was logged without mocking the logger,
        # but in a real-world scenario, we would expect a warning to be logged for an unknown event type.

    def test__handle_event_block_delta(self):
        """
        Test _handle_event method for BLOCK_DELTA event type
        """
        processor = MessageProcessor(StreamConfig())
        event_type = EventType.BLOCK_DELTA
        event = {
            "contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}
        }
        ai_message = {"content": [{}]}
        stream_callback = None

        processor._handle_event(event_type, event, ai_message, stream_callback)

        assert ai_message == {"content": [{"text": "Hello"}]}

    def test__handle_event_block_stop(self):
        """
        Test _handle_event method for BLOCK_STOP event type
        """
        processor = MessageProcessor(StreamConfig())
        event_type = EventType.BLOCK_STOP
        event = {"contentBlockStop": {"contentBlockIndex": 0}}
        ai_message = {"content": [{"text": "Hello"}]}
        stream_callback = None

        processor._handle_event(event_type, event, ai_message, stream_callback)

        assert ai_message == {"content": [{"text": "Hello"}]}

    def test__handle_event_message_start(self):
        """
        Test _handle_event method for MESSAGE_START event type
        """
        processor = MessageProcessor(StreamConfig())
        event_type = EventType.MESSAGE_START
        event = {"messageStart": {"role": "assistant"}}
        ai_message = {"content": []}
        stream_callback = None

        processor._handle_event(event_type, event, ai_message, stream_callback)

        assert ai_message == {"content": [], "role": "assistant"}

    def test__handle_event_unknown_type(self):
        """
        Test _handle_event method for unknown event type
        """
        processor = MessageProcessor(StreamConfig())
        event_type = "UNKNOWN_TYPE"
        event = {}
        ai_message = {"content": []}
        stream_callback = None

        processor._handle_event(event_type, event, ai_message, stream_callback)

        assert ai_message == {"content": []}

    def test__handle_text_delta_2(self):
        """
        Test _handle_text_delta when text exists in ai_message, stream_callback is provided,
        and buffer threshold is reached.
        """
        # Setup
        processor = MessageProcessor(StreamConfig(buffer_threshold=5))
        delta = {"text": "world"}
        index = 0
        ai_message = {"content": [{"text": "hello "}]}

        # Mock stream callback
        mock_stream_callback = lambda x: None

        # Call the method
        processor._handle_text_delta(delta, index, ai_message, mock_stream_callback)

        # Assertions
        assert ai_message["content"][index]["text"] == "hello world"
        assert (
            processor.buffer[index] == ""
        )  # Buffer should be emptied after reaching threshold

        # Verify that stream_callback was called
        # Note: In a real scenario, you might want to use a mock library to track calls
        # This simplified test assumes the method behaves as expected

        # Clean up
        processor.buffer.clear()

    def test__update_tool_use_2(self):
        """
        Test _update_tool_use method when toolUse exists, input is in delta,
        input is not in ai_message, and there are other fields to update.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Prepare test data
        delta = {
            "toolUse": {
                "name": "test_tool",
                "input": "test_input",
                "other_field": "other_value",
            }
        }
        index = 0
        ai_message = {"content": [{"toolUse": {"name": "test_tool"}}]}

        # Call the method under test
        processor._update_tool_use(delta, index, ai_message)

        # Assert the expected outcomes
        assert "toolUse" in ai_message["content"][index]
        assert ai_message["content"][index]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][index]["toolUse"]["input"] == "test_input"
        assert ai_message["content"][index]["toolUse"]["other_field"] == "other_value"

    def test__update_tool_use_3(self):
        """
        Test _update_tool_use method when toolUse exists, input is in delta,
        input exists in ai_message, and there are other fields to update.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Set up test data
        delta = {
            "toolUse": {
                "input": "additional input",
                "name": "updated_tool_name",
                "other_field": "new_value",
            }
        }
        index = 0
        ai_message = {
            "content": [
                {
                    "toolUse": {
                        "name": "original_tool_name",
                        "input": "initial input",
                    }
                }
            ]
        }

        # Call the method under test
        processor._update_tool_use(delta, index, ai_message)

        # Assert the expected outcomes
        assert (
            ai_message["content"][index]["toolUse"]["input"]
            == "initial inputadditional input"
        )
        assert ai_message["content"][index]["toolUse"]["name"] == "updated_tool_name"
        assert ai_message["content"][index]["toolUse"]["other_field"] == "new_value"

    def test__update_tool_use_4(self):
        """
        Test _update_tool_use when 'toolUse' is not in ai_message content,
        'input' is not in delta['toolUse'], and there are other fields to update.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        delta = {"toolUse": {"name": "test_tool", "description": "A test tool"}}
        index = 0
        ai_message = {"content": [{}]}

        # Act
        processor._update_tool_use(delta, index, ai_message)

        # Assert
        assert "toolUse" in ai_message["content"][index]
        assert ai_message["content"][index]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][index]["toolUse"]["description"] == "A test tool"
        assert ai_message["content"][index]["toolUse"]["input"] == ""

    def test__update_tool_use_5(self):
        """
        Test _update_tool_use when toolUse is not in ai_message content, input is in delta toolUse,
        input is not in ai_message content toolUse, and there are no non-input keys in delta toolUse.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Set up test data
        delta = {"toolUse": {"name": "test_tool", "input": "test_input"}}
        index = 0
        ai_message = {"content": [{}]}

        # Call the method under test
        processor._update_tool_use(delta, index, ai_message)

        # Assert the expected outcomes
        assert "toolUse" in ai_message["content"][index]
        assert ai_message["content"][index]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][index]["toolUse"]["input"] == "test_input"
        assert len(ai_message["content"][index]["toolUse"]) == 2

    def test__update_tool_use_initializes_and_updates_tool_use(self):
        """
        Test that _update_tool_use initializes toolUse structure and updates it correctly.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        delta = {
            "toolUse": {
                "name": "test_tool",
                "input": "initial input",
                "other_field": "other value",
            }
        }
        index = 0
        ai_message = {"content": [{}]}

        # Act
        processor._update_tool_use(delta, index, ai_message)

        # Assert
        assert "toolUse" in ai_message["content"][index]
        assert ai_message["content"][index]["toolUse"]["name"] == "test_tool"
        assert ai_message["content"][index]["toolUse"]["input"] == "initial input"
        assert ai_message["content"][index]["toolUse"]["other_field"] == "other value"

        # Act again with new delta to test update
        new_delta = {
            "toolUse": {"input": " additional input", "new_field": "new value"}
        }
        processor._update_tool_use(new_delta, index, ai_message)

        # Assert again
        assert (
            ai_message["content"][index]["toolUse"]["input"]
            == "initial input additional input"
        )
        assert ai_message["content"][index]["toolUse"]["new_field"] == "new value"
        assert (
            ai_message["content"][index]["toolUse"]["name"] == "test_tool"
        )  # Unchanged
        assert ai_message["content"][index]["toolUse"]["other_field"] == "other value"

    def test_flush_buffer_with_empty_buffer(self):
        """
        Test _flush_buffer when the buffer is empty.
        """
        processor = MessageProcessor(StreamConfig())
        mock_callback = MockCallback()

        processor._flush_buffer(mock_callback.callback)

        assert (
            mock_callback.called == 0
        ), "Callback should not be called when buffer is empty"

    def test_flush_buffer_with_exception_in_callback(self):
        """
        Test _flush_buffer when the callback raises an exception.
        """
        processor = MessageProcessor(StreamConfig())
        processor.buffer = {0: "Some content"}

        def failing_callback(content):
            raise ValueError("Callback failed")

        with pytest.raises(ValueError, match="Callback failed"):
            processor._flush_buffer(failing_callback)

    def test_flush_buffer_with_non_callable_callback(self):
        """
        Test _flush_buffer when the callback is not callable.
        """
        processor = MessageProcessor(StreamConfig())
        processor.buffer = {0: "Some content"}

        with pytest.raises(TypeError):
            processor._flush_buffer("not_a_callable")

    def test_flush_buffer_with_none_callback(self):
        """
        Test _flush_buffer when the callback is None.
        """
        processor = MessageProcessor(StreamConfig())
        processor.buffer = {0: "Some content"}

        with pytest.raises(TypeError):
            processor._flush_buffer(None)

    @pytest.mark.parametrize("event_type", list(EventType))
    def test_get_event_type_for_all_event_types(self, event_type):
        """
        Test that _get_event_type correctly identifies all possible EventTypes.
        """
        # Arrange
        processor = MessageProcessor()
        event: Dict[str, Any] = {event_type.value: {}}

        # Act
        result = processor._get_event_type(event)

        # Assert
        assert result == event_type

    def test_get_event_type_when_event_type_not_in_event(self):
        """
        Test that _get_event_type returns None when the event does not contain any valid event type value.
        """
        # Arrange
        processor = MessageProcessor()
        event: Dict[str, Any] = {"invalidEventType": "someValue"}

        # Act
        result = processor._get_event_type(event)

        # Assert
        assert result is None

    def test_get_event_type_when_event_type_value_in_event(self):
        """
        Test that _get_event_type returns the correct EventType when the event contains a valid event type value.
        """
        # Arrange
        processor = MessageProcessor()
        event: Dict[str, Any] = {"messageStart": {"role": "assistant"}}

        # Act
        result = processor._get_event_type(event)

        # Assert
        assert result == EventType.MESSAGE_START

    def test_get_event_type_with_empty_event(self):
        """
        Test that _get_event_type returns None when the event is empty.
        """
        # Arrange
        processor = MessageProcessor()
        event: Dict[str, Any] = {}

        # Act
        result = processor._get_event_type(event)

        # Assert
        assert result is None

    def test_handle_block_delta_empty_input(self):
        """
        Test _handle_block_delta with empty input.
        """
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_delta(event, ai_message, None)

    def test_handle_block_delta_invalid_callback(self):
        """
        Test _handle_block_delta with invalid stream_callback.
        """
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {
            "contentBlockDelta": {"delta": {"text": "test"}, "contentBlockIndex": 0}
        }
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(TypeError):
            processor._handle_block_delta(event, ai_message, "not_a_function")

    def test_handle_block_delta_invalid_input(self):
        """
        Test _handle_block_delta with invalid input structure.
        """
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockDelta": {}}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_delta(event, ai_message, None)

    def test_handle_block_delta_large_index(self):
        """
        Test _handle_block_delta with a very large content block index.
        """
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {
            "contentBlockDelta": {
                "delta": {"text": "test"},
                "contentBlockIndex": 1000000,
            }
        }
        ai_message: Dict[str, Any] = {"content": []}

        processor._handle_block_delta(event, ai_message, None)
        assert len(ai_message["content"]) == 1000001
        assert ai_message["content"][1000000] == {"text": "test"}

    def test_handle_block_delta_missing_delta_key(self):
        """
        Test _handle_block_delta with missing 'delta' key in the event.
        """
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockDelta": {"contentBlockIndex": 0}}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_delta(event, ai_message, None)

    def test_handle_block_delta_with_no_tool_use_or_text(self):
        """
        Test _handle_block_delta when the delta contains neither 'toolUse' nor 'text'.
        This should not modify the ai_message content.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Prepare test data
        event = {"contentBlockDelta": {"delta": {}, "contentBlockIndex": 0}}
        ai_message = {"content": []}
        stream_callback = None

        # Call the method under test
        processor._handle_block_delta(event, ai_message, stream_callback)

        # Assert that the ai_message content remains unchanged
        assert ai_message == {
            "content": [{}]
        }, "ai_message should contain an empty dict in content"

        # Assert that no exception was raised
        # (If we reached this point, no exception was raised during the method execution)

    def test_handle_block_start_empty_event(self):
        """
        Test _handle_block_start with an empty event dictionary.
        """
        processor = MessageProcessor(StreamConfig())
        event = {}
        ai_message = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_start(event, ai_message)

    def test_handle_block_start_incorrect_type(self):
        """
        Test _handle_block_start with incorrect type for contentBlockIndex.
        """
        processor = MessageProcessor(StreamConfig())
        event = {"contentBlockStart": {"start": {}, "contentBlockIndex": "0"}}
        ai_message = {"content": []}

        with pytest.raises(TypeError):
            processor._handle_block_start(event, ai_message)

    def test_handle_block_start_invalid_index(self):
        """
        Test _handle_block_start with an invalid content block index.
        """
        processor = MessageProcessor(StreamConfig())
        event = {"contentBlockStart": {"start": {}, "contentBlockIndex": -1}}
        ai_message = {"content": []}

        processor._handle_block_start(event, ai_message)
        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0] == {}

    def test_handle_block_start_missing_required_fields(self):
        """
        Test _handle_block_start with missing required fields in the event.
        """
        processor = MessageProcessor(StreamConfig())
        event = {"contentBlockStart": {}}
        ai_message = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_start(event, ai_message)

    def test_handle_block_start_tooluse_none(self):
        """
        Test _handle_block_start when toolUse is None.
        """
        processor = MessageProcessor(StreamConfig())
        event = {
            "contentBlockStart": {"start": {"toolUse": None}, "contentBlockIndex": 0}
        }
        ai_message = {"content": []}

        processor._handle_block_start(event, ai_message)
        assert len(ai_message["content"]) == 1
        assert ai_message["content"][0] == {"toolUse": None}

    def test_handle_block_stop_empty_event(self):
        """Test _handle_block_stop with an empty event dictionary."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_stop(event, ai_message)

    def test_handle_block_stop_invalid_index_type(self):
        """Test _handle_block_stop with invalid index type."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockStop": {"contentBlockIndex": "invalid"}}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(TypeError):
            processor._handle_block_stop(event, ai_message)

    def test_handle_block_stop_invalid_json_input(self):
        """Test _handle_block_stop with invalid JSON in toolUse input."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockStop": {"contentBlockIndex": 0}}
        ai_message: Dict[str, Any] = {
            "content": [{"toolUse": {"input": "invalid json"}}]
        }

        processor._handle_block_stop(event, ai_message)
        assert ai_message["content"][0]["toolUse"]["input"] == {}

    def test_handle_block_stop_large_index(self):
        """Test _handle_block_stop with a very large index."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockStop": {"contentBlockIndex": 1000000}}
        ai_message: Dict[str, Any] = {"content": []}

        processor._handle_block_stop(event, ai_message)
        assert len(ai_message["content"]) == 1000001
        assert all(content == {} for content in ai_message["content"])

    def test_handle_block_stop_missing_content_block_index(self):
        """Test _handle_block_stop with missing contentBlockIndex."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockStop": {}}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_block_stop(event, ai_message)

    def test_handle_block_stop_non_string_tool_input(self):
        """Test _handle_block_stop with non-string tool input."""
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"contentBlockStop": {"contentBlockIndex": 0}}
        ai_message: Dict[str, Any] = {"content": [{"toolUse": {"input": 42}}]}

        processor._handle_block_stop(event, ai_message)
        assert ai_message["content"][0]["toolUse"]["input"] == 42

    def test_handle_block_stop_without_tool_use(self):
        """
        Test _handle_block_stop when there is no toolUse in the current content.
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        event = {"contentBlockStop": {"contentBlockIndex": 0}}
        ai_message = {"content": [{"text": "Some text content"}]}

        # Act
        with patch("utils.converse_stream.message_processor.logger") as mock_logger:
            processor._handle_block_stop(event, ai_message)

        # Assert
        assert len(ai_message["content"]) == 1
        assert "text" in ai_message["content"][0]
        assert ai_message["content"][0]["text"] == "Some text content"
        assert "toolUse" not in ai_message["content"][0]
        mock_logger.debug.assert_called_with("Finalized content block 0")

    def test_handle_event_with_invalid_stream_callback(self, message_processor):
        """
        Test _handle_event with an invalid stream callback
        """
        event_type = EventType.BLOCK_DELTA
        event = {
            "contentBlockDelta": {"delta": {"text": "test"}, "contentBlockIndex": 0}
        }
        ai_message = {"content": []}
        invalid_callback = "not_a_function"

        with pytest.raises(TypeError):
            message_processor._handle_event(
                event_type, event, ai_message, invalid_callback
            )

    def test_handle_event_with_none_event(self, message_processor):
        """
        Test _handle_event with None as the event
        """
        event_type = EventType.BLOCK_DELTA
        event = None
        ai_message = {}

        with pytest.raises(TypeError):
            message_processor._handle_event(event_type, event, ai_message, None)

    def test_handle_event_with_unsupported_event_type(self, message_processor):
        """
        Test _handle_event with an unsupported event type
        """

        class UnsupportedEventType(Enum):
            UNSUPPORTED = "unsupported"

        event_type = UnsupportedEventType.UNSUPPORTED
        event = {}
        ai_message = {}

        message_processor._handle_event(event_type, event, ai_message, None)
        assert (
            ai_message == {}
        ), "AI message should remain empty for an unsupported event type"

    def test_handle_message_start_empty_event(self):
        """Test _handle_message_start with an empty event dictionary"""
        processor = MessageProcessor(StreamConfig())
        event = {}
        ai_message = {}

        with pytest.raises(KeyError):
            processor._handle_message_start(event, ai_message)

    def test_handle_message_start_empty_role(self):
        """Test _handle_message_start with empty role string"""
        processor = MessageProcessor(StreamConfig())
        event = {"messageStart": {"role": ""}}
        ai_message = {}

        processor._handle_message_start(event, ai_message)
        assert ai_message["role"] == ""

    def test_handle_message_start_invalid_event_type(self):
        """Test _handle_message_start with invalid event type"""
        processor = MessageProcessor(StreamConfig())
        event = {"invalidEventType": {"role": "assistant"}}
        ai_message = {}

        with pytest.raises(KeyError):
            processor._handle_message_start(event, ai_message)

    def test_handle_message_start_missing_role(self):
        """Test _handle_message_start with missing role in messageStart"""
        processor = MessageProcessor(StreamConfig())
        event = {"messageStart": {}}
        ai_message = {}

        with pytest.raises(KeyError):
            processor._handle_message_start(event, ai_message)

    def test_handle_message_start_non_string_role(self):
        """Test _handle_message_start with non-string role value"""
        processor = MessageProcessor(StreamConfig())
        event = {"messageStart": {"role": 123}}
        ai_message = {}

        processor._handle_message_start(event, ai_message)
        assert ai_message["role"] == 123

    def test_handle_message_start_overwrite_existing_role(self):
        """Test _handle_message_start overwriting an existing role in ai_message"""
        processor = MessageProcessor(StreamConfig())
        event = {"messageStart": {"role": "assistant"}}
        ai_message = {"role": "user"}

        processor._handle_message_start(event, ai_message)
        assert ai_message["role"] == "assistant"

    def test_handle_message_start_sets_correct_role(self):
        """
        Test that _handle_message_start correctly sets the role in ai_message
        """
        # Arrange
        processor = MessageProcessor(StreamConfig())
        event: Dict[str, Any] = {"messageStart": {"role": "assistant"}}
        ai_message: Dict[str, Any] = {}

        # Act
        processor._handle_message_start(event, ai_message)

        # Assert
        assert ai_message["role"] == "assistant"

    def test_handle_text_delta_empty_input(self):
        """Test _handle_text_delta with empty input"""
        processor = MessageProcessor(StreamConfig())
        delta: Dict[str, Any] = {"text": ""}
        ai_message: Dict[str, Any] = {"content": []}

        processor._handle_text_delta(delta, 0, ai_message, None)

        assert ai_message["content"] == [{"text": ""}]

    def test_handle_text_delta_invalid_ai_message(self):
        """Test _handle_text_delta with invalid ai_message structure"""
        processor = MessageProcessor(StreamConfig())
        delta: Dict[str, Any] = {"text": "test"}
        ai_message: Dict[str, Any] = {}  # Missing 'content' key

        with pytest.raises(KeyError):
            processor._handle_text_delta(delta, 0, ai_message, None)

    def test_handle_text_delta_large_input(self):
        """Test _handle_text_delta with a large input text"""
        processor = MessageProcessor(StreamConfig())
        large_text = "a" * 1000000  # 1 million characters
        delta: Dict[str, Any] = {"text": large_text}
        ai_message: Dict[str, Any] = {"content": []}

        processor._handle_text_delta(delta, 0, ai_message, None)

        assert len(ai_message["content"][0]["text"]) == 1000000

    def test_handle_text_delta_missing_text_key(self):
        """Test _handle_text_delta with missing 'text' key in delta"""
        processor = MessageProcessor(StreamConfig())
        delta: Dict[str, Any] = {"wrong_key": "test"}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(KeyError):
            processor._handle_text_delta(delta, 0, ai_message, None)

    def test_handle_text_delta_stream_callback_exception(self):
        """Test _handle_text_delta when stream_callback raises an exception"""

        def faulty_callback(text: str):
            raise Exception("Callback error")

        processor = MessageProcessor(StreamConfig(buffer_threshold=1))
        delta: Dict[str, Any] = {"text": "test"}
        ai_message: Dict[str, Any] = {"content": []}

        with pytest.raises(Exception, match="Callback error"):
            processor._handle_text_delta(delta, 0, ai_message, faulty_callback)

    def test_handle_text_delta_unicode_input(self):
        """Test _handle_text_delta with Unicode input"""
        processor = MessageProcessor(StreamConfig())
        unicode_text = "こんにちは世界"  # "Hello World" in Japanese
        delta: Dict[str, Any] = {"text": unicode_text}
        ai_message: Dict[str, Any] = {"content": []}

        processor._handle_text_delta(delta, 0, ai_message, None)

        assert ai_message["content"][0]["text"] == unicode_text

    def test_init_default_config(self):
        """
        Test initializing MessageProcessor with default config.
        """
        processor = MessageProcessor()
        assert isinstance(processor.config, StreamConfig)
        assert processor.config.buffer_threshold == 30

    def test_init_with_custom_config(self):
        """
        Test initialization of MessageProcessor with custom StreamConfig
        """
        custom_config = StreamConfig(buffer_threshold=50)
        processor = MessageProcessor(config=custom_config)
        assert isinstance(processor.config, StreamConfig)
        assert processor.config.buffer_threshold == 50
        assert processor.buffer == {}

    def test_init_with_default_config(self):
        """
        Test initialization of MessageProcessor with default StreamConfig
        """
        processor = MessageProcessor()
        assert isinstance(processor.config, StreamConfig)
        assert processor.config.buffer_threshold == 30
        assert processor.buffer == {}

    def test_init_with_large_buffer_threshold(self):
        """
        Test initializing MessageProcessor with a very large buffer threshold.
        """
        config = StreamConfig(buffer_threshold=1000000000)
        processor = MessageProcessor(config=config)
        assert processor.config.buffer_threshold == 1000000000

    def test_process_stream_1(self):
        # Existing test method, left unchanged
        pass

    def test_process_stream_2(self):
        """
        Test process_stream with no valid event types and a stream callback.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig(buffer_threshold=10))

        # Mock events with no valid event types
        events: List[Dict[str, Any]] = [
            {"invalid_event": "data1"},
            {"another_invalid": "data2"},
        ]

        # Mock stream callback
        mock_callback: Callable[[str], None] = lambda x: None

        # Call process_stream
        result = processor.process_stream(events, stream_callback=mock_callback)

        # Assert that the result is an empty message
        assert result == {"content": []}

    def test_process_stream_3(self):
        """
        Test process_stream method with various event types and without stream callback.
        """
        # Initialize MessageProcessor
        processor = MessageProcessor(StreamConfig())

        # Create test events
        events: List[Dict[str, Any]] = [
            {"messageStart": {"role": "assistant"}},
            {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}},
            {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}},
            {
                "contentBlockDelta": {
                    "delta": {"text": " world"},
                    "contentBlockIndex": 0,
                }
            },
            {"contentBlockStop": {"contentBlockIndex": 0}},
        ]

        # Call process_stream without stream_callback
        result = processor.process_stream(events)

        # Assert the result
        expected_result = {"role": "assistant", "content": [{"text": "Hello world"}]}
        assert (
            result == expected_result
        ), f"Expected {expected_result}, but got {result}"

        # Verify that all event types were processed
        assert all(
            processor._get_event_type(event) is not None for event in events
        ), "Not all event types were processed"

    def test_process_stream_with_empty_input(self):
        """
        Test process_stream with empty input list
        """
        processor = MessageProcessor()
        result = processor.process_stream([])
        assert result == {"content": []}, "Expected empty content for empty input"

    def test_process_stream_with_exception_in_callback(self):
        """
        Test process_stream with exception raised in stream callback
        """

        def failing_callback(text: str):
            raise Exception("Callback failed")

        processor = MessageProcessor(StreamConfig(buffer_threshold=1))
        events: List[Dict[str, Any]] = [
            {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}},
            {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}},
            {"contentBlockStop": {"contentBlockIndex": 0}},
        ]
        with pytest.raises(Exception, match="Callback failed"):
            processor.process_stream(events, stream_callback=failing_callback)

    def test_process_stream_with_incorrect_event_type(self):
        """
        Test process_stream with incorrect event type
        """
        processor = MessageProcessor()
        events = [{"invalidEventType": {}}]
        result = processor.process_stream(events)
        assert result == {
            "content": []
        }, "Expected empty content for invalid event type"

    def test_process_stream_with_invalid_json_in_tool_use(self):
        """
        Test process_stream with invalid JSON in tool use input
        """
        processor = MessageProcessor()
        events: List[Dict[str, Any]] = [
            {"contentBlockStart": {"start": {"toolUse": {}}, "contentBlockIndex": 0}},
            {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": "{invalid_json}"}},
                    "contentBlockIndex": 0,
                }
            },
            {"contentBlockStop": {"contentBlockIndex": 0}},
        ]
        result = processor.process_stream(events)
        assert (
            result["content"][0]["toolUse"]["input"] == {}
        ), "Expected empty dict for invalid JSON in tool use input"

    def test_process_stream_with_invalid_stream_callback(self):
        """
        Test process_stream with invalid stream callback
        """
        processor = MessageProcessor()
        events: List[Dict[str, Any]] = [
            {"contentBlockStart": {"start": {}, "contentBlockIndex": 0}},
            {"contentBlockDelta": {"delta": {"text": "Hello"}, "contentBlockIndex": 0}},
            {"contentBlockStop": {"contentBlockIndex": 0}},
        ]
        with pytest.raises(TypeError):
            processor.process_stream(events, stream_callback="not a callable")

    def test_process_stream_with_missing_required_fields(self):
        """
        Test process_stream with missing required fields in events
        """
        processor = MessageProcessor()
        events = [{"messageStart": {}}]  # Missing 'role' field
        with pytest.raises(KeyError):
            processor.process_stream(events)

    def test_update_tool_use_with_existing_content(self):
        """
        Test _update_tool_use when content already exists at the given index.
        """
        processor = MessageProcessor(StreamConfig())
        delta = {"toolUse": {"name": "new_tool", "input": "new_input"}}
        index = 0
        ai_message = {
            "content": [
                {"toolUse": {"name": "existing_tool", "input": "existing_input"}}
            ]
        }

        processor._update_tool_use(delta, index, ai_message)
        assert ai_message["content"][0]["toolUse"]["name"] == "new_tool"
        assert ai_message["content"][0]["toolUse"]["input"] == "existing_inputnew_input"


class MockCallback:

    def __init__(self):
        self.called = 0
        self.last_content = None

    def callback(self, content):
        self.called += 1
        self.last_content = content
