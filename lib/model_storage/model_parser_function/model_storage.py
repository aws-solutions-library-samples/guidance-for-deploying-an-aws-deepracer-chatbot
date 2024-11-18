from typing import Any, Dict

import boto3
import dynamo_helpers
from botocore.exceptions import ClientError


class ModelStorage:
    def __init__(self, ddb_table_name: str, boto3_session: boto3.Session = None):
        if boto3_session:
            dynamodb = boto3_session.resource("dynamodb")
        else:
            dynamodb = boto3.resource("dynamodb")

        self.ddbTable = dynamodb.Table(ddb_table_name)

    def add_model(
        self, user_id: str, model_name: str, model_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store a model in a DynamoDB table.

        Args:
            user_id (str): The ID of the user.
            model_name (str): The name of the model.
            model_data (Dict[str, Any]): The model data to be stored.

        Returns:
            Dict[str, Any]: The updated item in the DynamoDB table.
        """

        ddb_update_expressions = dynamo_helpers.generate_update_query(model_data)

        try:
            response = self.ddbTable.update_item(
                Key={"userId": user_id, "modelName": model_name},
                UpdateExpression=ddb_update_expressions["UpdateExpression"],
                ExpressionAttributeNames=ddb_update_expressions[
                    "ExpressionAttributeNames"
                ],
                ExpressionAttributeValues=ddb_update_expressions[
                    "ExpressionAttributeValues"
                ],
                ReturnValues="ALL_NEW",
            )
            updated_item = response["Attributes"]

            return updated_item
        except ClientError as e:
            print("Error storing model in DynamoDB", e)

    def get_model(self, user_id: str, model_name: str):
        """
        Fetch a stored model from DynamoDB.

        Args:
            key (Dict[str, Union[str, int]]): The primary key of the item to fetch.

        Returns:
            Union[Dict, None]: The deserialized item if found, or None if not found.
        """
        try:
            response = self.ddbTable.get_item(
                Key={"userId": user_id, "modelName": model_name},
            )
            if "Item" in response:
                return {
                    k: dynamo_helpers.replace_decimal_with_float(v)
                    for k, v in response["Item"].items()
                }
            return None
        except ClientError as e:
            print(f"Error fetching item from DynamoDB: {e}")
            raise

    def list_models(self, user_id: str) -> dict:
        """
        Lists all models for the given user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: A dictionary containing a list of model names for the user.
        """
        try:
            # Define the query parameters
            query_params = {
                "KeyConditionExpression": "#uid = :uid",
                "ExpressionAttributeNames": {"#uid": "userId"},
                "ExpressionAttributeValues": {":uid": user_id},
            }

            # Perform the query
            response = self.ddbTable.query(**query_params)

            # Extract the items from the response
            models = response.get("Items", [])

            # If there are no models, return an empty list
            if not models:
                return {"Models": []}

            # Process the models to a more friendly format
            processed_models = [model["modelName"] for model in models]

            return {"Models": processed_models}

        except Exception as e:
            print(f"Error listing model data: {e}")
            return {"Error": f"Error listing model data: {e}"}
