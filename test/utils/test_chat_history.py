import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from utils.chat_history import ChatHistory
from utils.dynamo_helpers import replace_decimal_with_float, replace_floats_with_decimal


class TestChatHistory:

    @pytest.fixture(autouse=True)
    def aws_credentials(self):
        """Mocked AWS Credentials for moto."""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    @pytest.fixture
    def chat_history(self, aws_credentials):
        table_name = "test_chat_history"
        return ChatHistory(table_name)

    def test__get_keys_returns_correct_dictionary(self):
        """
        Test that _get_keys returns a dictionary with correct keys and values.
        """
        # Arrange
        user_id = "test_user"
        session_id = "test_session"

        # Act
        result = ChatHistory._get_keys(user_id, session_id)

        # Assert
        expected = {
            "userId": user_id,
            "sessionId": session_id,
        }
        assert result == expected, f"Expected {expected}, but got {result}"

    def test__get_keys_with_empty_inputs(self):
        """
        Test _get_keys method with empty inputs.
        """
        result = ChatHistory._get_keys("", "")
        assert result == {"userId": "", "sessionId": ""}

    def test__get_keys_with_long_inputs(self):
        """
        Test _get_keys method with very long string inputs.
        """
        long_string = "a" * 1000000
        result = ChatHistory._get_keys(long_string, long_string)
        assert result == {"userId": long_string, "sessionId": long_string}

    def test__get_keys_with_special_characters(self):
        """
        Test _get_keys method with special characters in inputs.
        """
        special_chars = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/~`"
        result = ChatHistory._get_keys(special_chars, special_chars)
        assert result == {"userId": special_chars, "sessionId": special_chars}

    def test__get_keys_with_unicode_characters(self):
        """
        Test _get_keys method with unicode characters in inputs.
        """
        unicode_chars = "こんにちは世界"
        result = ChatHistory._get_keys(unicode_chars, unicode_chars)
        assert result == {"userId": unicode_chars, "sessionId": unicode_chars}

    @mock_aws
    def test_init_with_custom_boto3_session(self):
        """
        Test initialization of ChatHistory with a custom boto3 session.
        """
        # Set up mock DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        dynamodb.create_table(
            TableName="test_table",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "sessionId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "sessionId", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Create a custom boto3 session
        custom_session = boto3.Session(region_name="us-west-2")

        # Initialize ChatHistory with custom session
        chat_history = ChatHistory("test_table", boto3_session=custom_session)

        # Assert that the DynamoDB table is correctly set
        assert chat_history.ddb_table.name == "test_table"
        assert chat_history.ddb_table.meta.client.meta.region_name == "us-west-2"

    def test_init_with_invalid_boto3_session(self):
        """
        Test initializing ChatHistory with an invalid boto3 session.
        """
        invalid_session = "not a boto3 session"
        with pytest.raises(AttributeError):
            ChatHistory("valid_table", boto3_session=invalid_session)

    @mock_aws
    def test_init_without_boto3_session(self):
        """
        Test initialization of ChatHistory without a custom boto3 session.
        """
        # Set up mock DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="test_table",
            KeySchema=[
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "sessionId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "userId", "AttributeType": "S"},
                {"AttributeName": "sessionId", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )

        # Initialize ChatHistory without custom session
        chat_history = ChatHistory("test_table")

        # Assert that the DynamoDB table is correctly set
        assert chat_history.ddb_table.name == "test_table"
        assert chat_history.ddb_table.meta.client.meta.region_name == "us-east-1"

    def test_load_empty_chat_history(self):
        """
        Test the load method when no chat history is found for the given user and session.
        """
        # Mock the DynamoDB table
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # Simulate no item found

        # Create a ChatHistory instance with the mock table
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = mock_table

        # Call the load method
        result = chat_history.load("user123", "session456")

        # Assert that the result is an empty list
        assert result == []

        # Verify that get_item was called with the correct parameters
        mock_table.get_item.assert_called_once_with(
            Key={"userId": "user123", "sessionId": "session456"},
            ProjectionExpression="messages",
        )

    def test_load_exception_handling(self, chat_history, monkeypatch):
        """Test load method exception handling"""

        def mock_get_item(*args, **kwargs):
            raise ClientError(
                {"Error": {"Code": "InternalServerError", "Message": "Test error"}},
                "get_item",
            )

        monkeypatch.setattr(chat_history.ddb_table, "get_item", mock_get_item)

        with pytest.raises(ClientError):
            chat_history.load("user1", "session1")

    def test_update_dynamodb_exception(self):
        """
        Test update method when DynamoDB raises an exception.
        """
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = MagicMock()
        chat_history.ddb_table.update_item.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InternalServerError",
                    "Message": "Internal Server Error",
                }
            },
            "UpdateItem",
        )

        with pytest.raises(ClientError):
            chat_history.update("user1", "session1", [{"message": "test"}])

    def test_update_updates_chat_history_successfully(self):
        """
        Test that the update method successfully updates the chat history for a given user and session.
        """
        # Mock DynamoDB table
        mock_table = MagicMock()

        # Create ChatHistory instance with mocked table
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = mock_table

        # Test data
        user_id = "test_user"
        session_id = "test_session"
        messages = [
            {"role": "user", "content": "Hello"},
            {
                "role": "assistant",
                "content": "Hi there!",
                "metadata": {"confidence": 0.95},
            },
        ]

        # Call the update method
        chat_history.update(user_id, session_id, messages)

        # Assert that update_item was called with correct arguments
        mock_table.update_item.assert_called_once_with(
            Key={"userId": user_id, "sessionId": session_id},
            UpdateExpression="SET #messages = :messages",
            ExpressionAttributeNames={"#messages": "messages"},
            ExpressionAttributeValues={
                ":messages": replace_floats_with_decimal(messages)
            },
            ReturnValues="ALL_NEW",
        )

    @patch("utils.chat_history.replace_floats_with_decimal")
    def test_update_with_float_conversion_error(self, mock_replace_floats):
        """
        Test update method when float conversion fails.
        """
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = MagicMock()
        mock_replace_floats.side_effect = ValueError("Float conversion error")

        with pytest.raises(ValueError):
            chat_history.update(
                "user1", "session1", [{"message": "test", "value": 1.23}]
            )

    def test_update_with_large_message_list(self):
        """
        Test update method with a large list of messages.
        """
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = MagicMock()

        large_message_list = [{"message": f"test{i}"} for i in range(1000)]

        try:
            chat_history.update("user1", "session1", large_message_list)
        except Exception as e:
            pytest.fail(f"Update with large message list failed: {str(e)}")

    def test_update_with_special_characters(self):
        """
        Test update method with special characters in inputs.
        """
        chat_history = ChatHistory("test_table")
        chat_history.ddb_table = MagicMock()

        try:
            chat_history.update(
                "user@#$%", "session&*()_+", [{"message": "test!@#$%^&*()"}]
            )
        except Exception as e:
            pytest.fail(f"Update with special characters failed: {str(e)}")
