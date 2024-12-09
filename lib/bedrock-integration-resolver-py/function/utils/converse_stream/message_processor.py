import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from aws_lambda_powertools import Logger

logger = Logger()


class EventType(Enum):
    MESSAGE_START = "messageStart"
    BLOCK_START = "contentBlockStart"
    BLOCK_DELTA = "contentBlockDelta"
    BLOCK_STOP = "contentBlockStop"


@dataclass
class StreamConfig:
    """Configuration for stream processing"""

    buffer_threshold: int = 30  # Characters to buffer before streaming


@dataclass
class ToolResult:
    """Structure for tool processing results"""

    tool_use_id: str
    content: List[Dict[str, Any]]
    status: str


class MessageProcessor:
    """
    Processes streaming responses from Bedrock ConverseStream API.

    This class handles the parsing and processing of different event types from
    the Bedrock ConverseStream API, including message content, tool usage, and
    streaming callbacks.

    Attributes:
        config (StreamConfig): Configuration for stream processing

    Example:
        ```python
        # Initialize processor
        processor = MessageProcessor(StreamConfig(buffer_threshold=50))

        # Define streaming callback
        def on_text(text: str):
            print(f"Streaming chunk: {text}")

        # Process stream
        result = processor.process_stream(
            events=bedrock_converse_stream_events,
            stream_callback=on_text
        )
        ```
    """

    def __init__(self, config: StreamConfig = StreamConfig()):
        """
        Initialize the message processor.

        Args:
            config (StreamConfig): Configuration settings for stream processing
        """
        self.config = config
        self.buffer = {}

    def process_stream(
        self,
        events: List[Dict[str, Any]],
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process a stream of events from Bedrock ConverseStream API. The generated text can optionally be streamed to the stream_callback function.

        Args:
            events: List of event dictionaries from Bedrock
            stream_callback: Optional callback function for streaming text output

        Returns:
            Dict containing the final assembled message

        Raises:
            KeyError: If required event fields are missing
        """

        ai_message = {"content": []}

        logger.debug("Starting to process stream events")
        for event in events:
            logger.debug(f"Processing event: {event}")
            print(event)
            event_type = self._get_event_type(event)
            if event_type:
                self._handle_event(event_type, event, ai_message, stream_callback)
                logger.debug(f"Current message content: {ai_message['content']}")

        if stream_callback:
            self._flush_buffer(stream_callback)

        logger.debug(f"Final message content: {ai_message['content']}")
        return ai_message

    def _get_event_type(self, event: Dict[str, Any]) -> Optional[EventType]:
        """Identifies the type of streaming event"""
        for event_type in EventType:
            if event_type.value in event:
                return event_type
        return None

    def _handle_event(
        self,
        event_type: EventType,
        event: Dict[str, Any],
        ai_message: Dict[str, Any],
        stream_callback: Optional[Callable[[str], None]],
    ):
        """Route events to appropriate handlers"""

        # Validate stream_callback if provided
        if stream_callback is not None and not callable(stream_callback):
            raise TypeError("stream_callback must be callable or None")

        handlers = {
            EventType.MESSAGE_START: lambda: self._handle_message_start(
                event, ai_message
            ),
            EventType.BLOCK_START: lambda: self._handle_block_start(event, ai_message),
            EventType.BLOCK_DELTA: lambda: self._handle_block_delta(
                event, ai_message, stream_callback
            ),
            EventType.BLOCK_STOP: lambda: self._handle_block_stop(event, ai_message),
        }

        handler = handlers.get(event_type)
        if handler:
            logger.debug(f"Handling event type: {event_type}")
            handler()
        else:
            logger.warning(f"No handler found for event type: {event_type}")

    def _handle_message_start(self, event: Dict[str, Any], ai_message: Dict[str, Any]):
        """Handle the message start event"""
        ai_message["role"] = event["messageStart"]["role"]

    def _handle_block_start(self, event: Dict[str, Any], ai_message: Dict[str, Any]):
        """
        Handles the initialization of a new content block in the message stream.

        This method processes contentBlockStart events from the Bedrock ConverseStream API,
        setting up the initial structure for new content blocks, particularly for tool
        use scenarios.

        Args:
            event (Dict[str, Any]): The block start event from the stream.
                Expected format:
                {
                    "contentBlockStart": {
                        "start": {
                            "toolUse": Dict[str, Any] | None,
                            ... other potential start data
                        },
                        "contentBlockIndex": int
                    }
                }
            ai_message (Dict[str, Any]): The message structure being built.
                Expected format:
                {
                    "content": [
                        {
                            "toolUse": Dict[str, Any] | None,
                            "text": str | None
                        },
                        ...
                    ]
                }
        """
        start_data = event["contentBlockStart"]["start"]
        index = event["contentBlockStart"]["contentBlockIndex"]

        content = {"toolUse": start_data["toolUse"]} if "toolUse" in start_data else {}
        ai_message["content"].insert(index, content)

    def _handle_block_delta(
        self,
        event: Dict[str, Any],
        ai_message: Dict[str, Any],
        stream_callback: Optional[Callable[[str], None]],
    ):
        """
        Processes content block delta events from the Bedrock ConverseStream API.

        This method handles incremental updates (deltas) in the stream, managing both
        text content and tool use updates. It routes the processing based on the type
        of delta received (text or tool use) and maintains the message structure.

        Args:
            event (Dict[str, Any]): The delta event from the stream.
                Expected format:
                {
                    "contentBlockDelta": {
                        "delta": {
                            "text": str | None,
                            "toolUse": Dict[str, Any] | None
                        },
                        "contentBlockIndex": int
                    }
                }
            ai_message (Dict[str, Any]): The message structure being built.
                Expected format:
                {
                    "content": [
                        {
                            "text": str | None,
                            "toolUse": Dict[str, Any] | None
                        },
                        ...
                    ]
                }
            stream_callback (Optional[Callable[[str], None]]): Optional callback function
                for streaming text content as it arrives.
        """

        # Validate stream_callback if provided
        if stream_callback is not None and not callable(stream_callback):
            raise TypeError("stream_callback must be callable or None")

        delta = event["contentBlockDelta"]["delta"]
        index = event["contentBlockDelta"]["contentBlockIndex"]

        logger.debug(f"Processing delta: {delta} at index {index}")

        # Ensure the content list has enough elements
        while len(ai_message["content"]) <= index:
            ai_message["content"].append({})

        if "toolUse" in delta:
            self._update_tool_use(delta, index, ai_message)
        elif "text" in delta:
            self._handle_text_delta(delta, index, ai_message, stream_callback)

        logger.debug(f"After delta processing: {ai_message['content']}")

    def _handle_block_stop(self, event: Dict[str, Any], ai_message: Dict[str, Any]):
        """
        Finalizes a content block in the message stream and processes any tool use content.

        This method handles contentBlockStop events from the Bedrock ConverseStream API,
        performing final processing steps such as JSON parsing for tool inputs and
        content validation. It's particularly important for ensuring tool use content
        is properly formatted before the block is finalized.

        Args:
            event (Dict[str, Any]): The block stop event from the stream.
                Expected format:
                {
                    "contentBlockStop": {
                        "contentBlockIndex": int
                    }
                }
            ai_message (Dict[str, Any]): The message structure to finalize.
                Expected format:
                {
                    "content": [
                        {
                            "toolUse": {
                                "name": str,
                                "input": str | Dict[str, Any],
                                ...other_fields
                            } | None,
                            "text": str | None
                        },
                        ...
                    ]
                }
        """
        index = event["contentBlockStop"]["contentBlockIndex"]

        # Ensure the content list has enough elements
        while len(ai_message["content"]) <= index:
            ai_message["content"].append({})

        current_content = ai_message["content"][index]

        # Finalize tool use content if present
        if "toolUse" in current_content:
            try:
                # Convert string input to JSON if it's a string
                if isinstance(current_content["toolUse"]["input"], str):
                    logger.debug(
                        f"Parsing tool input: {current_content['toolUse']['input']}"
                    )
                    current_content["toolUse"]["input"] = json.loads(
                        current_content["toolUse"]["input"]
                    )
                    logger.debug(
                        f"Parsed tool input: {current_content['toolUse']['input']}"
                    )
            except json.JSONDecodeError:
                logger.error(
                    f"Failed to parse tool input: {current_content['toolUse']['input']}"
                )
                current_content["toolUse"]["input"] = {}

        # Update the content block with finalized content
        ai_message["content"][index] = current_content
        logger.debug(f"Finalized content block {index}")

    def _update_tool_use(
        self, delta: Dict[str, Any], index: int, ai_message: Dict[str, Any]
    ):
        """
        Updates the tool use content in the AI message based on incoming delta events.

        This method handles the incremental updates for tool usage in the model's response,
        including tool names, inputs, and other tool-related fields. It manages both
        initial tool setup and subsequent updates.

        Args:
            delta (Dict[str, Any]): The delta event containing tool use updates.
                Expected format:
                {
                    "toolUse": {
                        "name": "tool_name",
                        "input": "tool_input_chunk",
                        ...other_fields
                    }
                }
            index (int): The index of the content block to update.
            ai_message (Dict[str, Any]): The message structure to update.
                Expected format:
                {
                    "content": [
                        {
                            "toolUse": {
                                "name": "tool_name",
                                "input": "accumulated_input",
                                ...other_fields
                            }
                        }
                    ]
                }
        """
        try:
            # Ensure the content list has enough elements
            while len(ai_message["content"]) <= index:
                ai_message["content"].append({})

            # Initialize toolUse structure if it doesn't exist
            if "toolUse" not in ai_message["content"][index]:
                ai_message["content"][index]["toolUse"] = {
                    "name": delta["toolUse"].get("name", ""),
                    "input": "",
                }

            # Update the input if it exists in the delta
            if "input" in delta["toolUse"]:
                if "input" not in ai_message["content"][index]["toolUse"]:
                    ai_message["content"][index]["toolUse"]["input"] = ""
                ai_message["content"][index]["toolUse"]["input"] += delta["toolUse"][
                    "input"
                ]

            # Update other toolUse fields if they exist
            for key, value in delta["toolUse"].items():
                if key != "input":
                    ai_message["content"][index]["toolUse"][key] = value

        except Exception as e:
            logger.error(f"Error updating tool use: {e}", exc_info=True)
            logger.debug(f"Delta: {delta}")
            logger.debug(
                f"Current content: {ai_message['content'][index] if index < len(ai_message['content']) else 'index out of range'}"
            )

    def _handle_text_delta(
        self,
        delta: Dict[str, Any],
        index: int,
        ai_message: Dict[str, Any],
        stream_callback: Optional[Callable[[str], None]],
    ):
        """Handle text delta updates"""
        text = delta["text"]
        logger.debug(f"Processing text delta: {text} at index {index}")

        # Ensure the content list has enough elements
        while len(ai_message["content"]) <= index:
            ai_message["content"].append({})

        # Update the message content
        if "text" not in ai_message["content"][index]:
            ai_message["content"][index] = {
                "text": text
            }  # Changed to set the entire dict
        else:
            ai_message["content"][index]["text"] += text

        # Handle streaming if callback is provided
        if stream_callback:
            self.buffer[index] = self.buffer.get(index, "") + text
            if (
                len(self.buffer[index]) >= self.config.buffer_threshold
            ):  # Fixed to use config
                stream_callback(self.buffer[index])
                self.buffer[index] = ""

        logger.debug(f"After text delta: {ai_message['content']}")

    def _flush_buffer(self, stream_callback: Callable[[str], None]):
        """Flush any remaining content in the buffer"""
        for index, content in self.buffer.items():
            if content:
                stream_callback(content)
                self.buffer[index] = ""
