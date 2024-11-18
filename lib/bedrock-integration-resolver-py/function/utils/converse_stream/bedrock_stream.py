import base64
import json
import os
from typing import BinaryIO, Dict, Generator, List, Optional, Union

import boto3
from aws_lambda_powertools import Logger

logger = Logger()


class BedrockStream:
    """
    A class for interacting with the Bedrock runtime to generate chat responses using the converse_stream API.
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
        boto3_client: Optional[boto3.client] = None,
        region_name: Optional[str] = "us-west-2",
    ):
        """
        Initialize the BedrockChat instance.

        Args:
            model_id (str): The ID of the model to use for chat generation.
            boto3_client (boto3.client, optional): An existing Boto3 client instance.
            region_name (str, optional): The AWS region name.
        """
        self.model_id = model_id

        self.bedrock_boto3 = boto3_client or boto3.client(
            service_name="bedrock-runtime", region_name=region_name
        )

    def __call__(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        tool_list: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, None]:
        """
        Generate a chat response based on the provided messages.

        Args:
            messages (List[Dict]): A list of message dictionaries.
            system_prompt (Optional[str]): Optional system prompt.
            tool_list (Optional[List[Dict]]): Optional list of tools for the LLM.

        Yields:
            Dict: Parsed events from the stream.
        """

        yield from self._call_model(messages, system_prompt, tool_list)

    def _call_model(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None,
        tool_list: Optional[List[Dict]] = None,
    ) -> Generator[Dict, None, None]:
        """
        Call the Bedrock model to generate a chat response using the converse_stream API and yield parsed events.

        Args:
            messages (List[Dict]): A list of message dictionaries.
            system_prompt (str, Optional): The system prompt to use for chat generation.
            tool_list (List[Dict], optional): A list of tools to use for chat generation.

        Yields:
            Dict: Parsed events from the stream.
        """

        converse_kwargs = self._prepare_converse_kwargs(
            messages, system_prompt, tool_list
        )

        try:
            logger.debug(
                "Calling Bedrock model with stream output",
                extra={"body": converse_kwargs},
            )
            response = self.bedrock_boto3.converse_stream(**converse_kwargs)
            if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise Exception("Failed to call Bedrock model")

            yield from response["stream"]
        except Exception as e:
            logger.error("Error calling Bedrock model", exc_info=True)
            raise e

    def _prepare_converse_kwargs(
        self,
        messages: List[Dict],
        system_prompt: Optional[str],
        tool_list: Optional[List[Dict]],
    ) -> Dict:
        """
        Prepare the keyword arguments for the converse_stream API call.

        Args:
            messages (List[Dict]): A list of message dictionaries.
            system_prompt (Optional[str]): The system prompt to use for chat generation.
            tool_list (Optional[List[Dict]]): A list of tools to use for chat generation.

        Returns:
            Dict: The prepared keyword arguments.
        """
        converse_kwargs = {
            "modelId": self.model_id,
            "messages": messages,
            "inferenceConfig": {"maxTokens": 1500, "temperature": 0},
        }

        if system_prompt:
            converse_kwargs["system"] = [{"text": system_prompt}]

        if tool_list:
            converse_kwargs["toolConfig"] = {"tools": tool_list}

        return converse_kwargs
