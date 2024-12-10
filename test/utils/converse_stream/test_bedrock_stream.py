from typing import Dict, Generator, List, Optional
from unittest.mock import MagicMock, Mock, patch

import boto3
import botocore.client
import pytest
from botocore.exceptions import ClientError, NoRegionError
from moto import mock_aws
from utils.converse_stream.bedrock_stream import BedrockStream


class TestBedrockStream:

    @pytest.fixture
    def bedrock_stream(self, mock_bedrock_client):
        return BedrockStream(boto3_client=mock_bedrock_client)

    @pytest.fixture
    def bedrock_stream_2(self):
        return BedrockStream()

    @pytest.fixture
    def mock_bedrock_client(self):
        return Mock()

    def test_call_generates_response(self):
        """
        Test that __call__ method generates a response using _call_model method.
        """
        # Arrange
        mock_messages = [{"role": "user", "content": "Hello"}]
        mock_system_prompt = "You are a helpful assistant."
        mock_tool_list = [{"type": "function", "function": {"name": "get_weather"}}]

        mock_generator = (
            item
            for item in [
                {"type": "content_block", "text": "Hello! How can I assist you today?"}
            ]
        )

        bedrock_stream = BedrockStream()
        bedrock_stream._call_model = MagicMock(return_value=mock_generator)

        # Act
        result = list(bedrock_stream(mock_messages, mock_system_prompt, mock_tool_list))

        # Assert
        bedrock_stream._call_model.assert_called_once_with(
            mock_messages, mock_system_prompt, mock_tool_list
        )
        assert len(result) == 1
        assert result[0] == {
            "type": "content_block",
            "text": "Hello! How can I assist you today?",
        }

    @mock_aws
    def test_init_with_custom_values(self):
        """
        Test initialization of BedrockStream with custom values.
        """
        custom_model_id = "custom-model-id"
        custom_region = "us-east-1"
        custom_boto3_client = boto3.client("bedrock-runtime", region_name=custom_region)

        bedrock_stream = BedrockStream(
            model_id=custom_model_id,
            boto3_client=custom_boto3_client,
            region_name=custom_region,
        )

        assert bedrock_stream.model_id == custom_model_id
        assert bedrock_stream.bedrock_boto3 == custom_boto3_client
        assert bedrock_stream.bedrock_boto3.meta.region_name == custom_region

    @mock_aws
    def test_init_with_default_values(self):
        """
        Test initialization of BedrockStream with default values.
        """
        bedrock_stream = BedrockStream()

        assert bedrock_stream.model_id == "anthropic.claude-3-5-sonnet-20240620-v1:0"
        assert isinstance(bedrock_stream.bedrock_boto3, botocore.client.BaseClient)
        assert bedrock_stream.bedrock_boto3.meta.region_name == "us-west-2"

    def test_init_with_none_values(self):
        """
        Test initialization with None values for optional parameters.
        """
        with pytest.raises(TypeError, match="model_id cannot be None"):
            BedrockStream(model_id=None)

        with pytest.raises(TypeError, match="region_name cannot be None"):
            BedrockStream(region_name=None)
