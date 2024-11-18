from typing import Any, Dict, List

import boto3
from utils.dynamo_helpers import replace_decimal_with_float, replace_floats_with_decimal


class ChatHistory:
    def __init__(self, table_name: str, boto3_session=None) -> None:

        if boto3_session:
            dynamodb = boto3_session.resource("dynamodb")
        else:
            dynamodb = boto3.resource("dynamodb")

        self.ddb_table = dynamodb.Table(table_name)

    def update(self, user_id: str, session_id: str, messages: List[Dict[str, Any]]):
        """
        Update the chat history for the current user session.

        Args:
            user_id (str): The unique identifier for the user.
            session_id (str): The unique identifier for the user session.
            messages (List[Dict[str, Any]]): The list of message dictionaries representing the chat history.

        Returns:
            None

        Raises:
            None
        """
        keys = self._get_keys(user_id, session_id)

        decimal_converted_chat_messages = [
            replace_floats_with_decimal(message) for message in messages
        ]

        update_expression = "SET #messages = :messages"
        expression_attribute_names = {"#messages": "messages"}
        expression_attribute_values = {":messages": decimal_converted_chat_messages}

        self.ddb_table.update_item(
            Key=keys,
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="ALL_NEW",
        )

    def load(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the chat history for the current user session.

        Args:
            user_id (str): The unique identifier for the user.
            session_id (str): The unique identifier for the user session.

        Returns:
            List[Dict[str, Any]]: A list of message dictionaries representing the chat history.
            If no chat history is found, an empty list is returned.

        Raises:
            None
        """
        keys = self._get_keys(user_id, session_id)

        response = self.ddb_table.get_item(
            Key=keys,
            ProjectionExpression="messages",
        )

        chat_messages = []
        if "Item" in response:
            chat_messages = replace_decimal_with_float(response["Item"]["messages"])

        return chat_messages

    @staticmethod
    def _get_keys(user_id: str, session_id: str) -> Dict[str, str]:
        """
        Generate the key dictionary for DynamoDB operations.

        Args:
            user_id (str): The unique identifier for the user.
            session_id (str): The unique identifier for the user session.

        Returns:
            Dict[str, str]: A dictionary containing the keys for DynamoDB operations.
        """
        return {
            "userId": user_id,
            "sessionId": session_id,
        }
