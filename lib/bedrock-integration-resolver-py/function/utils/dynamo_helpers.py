from decimal import ROUND_DOWN, Decimal
from typing import Dict, Union

import boto3
from aws_lambda_powertools import Logger
from boto3.dynamodb.types import Binary
from botocore.exceptions import ClientError

ddb_client = boto3.client("dynamodb", region_name="us-west-2")

logger = Logger()


def generate_update_query(fields, key_fields=[]):
    exp = {
        "UpdateExpression": "set",
        "ExpressionAttributeNames": {},
        "ExpressionAttributeValues": {},
    }
    ddb_attributes = replace_floats_with_decimal(fields)
    for key, value in ddb_attributes.items():
        if key not in key_fields:
            exp["UpdateExpression"] += f" #{key} = :{key},"
            exp["ExpressionAttributeNames"][f"#{key}"] = key
            exp["ExpressionAttributeValues"][f":{key}"] = value
    exp["UpdateExpression"] = exp["UpdateExpression"][0:-1]
    logger.info("DDB update expression", extra={"body": exp})
    return exp


def replace_decimal_with_float(
    obj: Union[Decimal, list, dict]
) -> Union[int, float, list, dict]:
    """
    Recursively converts Decimal types to int or float.

    Args:
        obj (Union[Decimal, list, dict]): The input object to be converted.

    Returns:
        Union[int, float, list, dict]: The converted object.
    """
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, list):
        return [replace_decimal_with_float(item) for item in obj]
    elif isinstance(obj, Binary):  # Convert the Binary object to a byte string
        byte_string = obj.value
        return byte_string
    elif isinstance(obj, dict):
        return {key: replace_decimal_with_float(value) for key, value in obj.items()}
    return obj


def replace_floats_with_decimal(
    obj: Union[float, list, dict]
) -> Union[Decimal, list, dict]:
    """
    Recursively replace floats with Decimal objects.

    Args:
        obj (Union[float, list, dict]): The input object to be processed.

    Returns:
        Union[decimal.Decimal, list, dict]: The processed object with floats replaced by Decimal objects.
    """
    if isinstance(obj, float):
        return Decimal(str(obj)).quantize(Decimal(".0001"), rounding=ROUND_DOWN)
    elif isinstance(obj, list):
        return [replace_floats_with_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: replace_floats_with_decimal(value) for key, value in obj.items()}
    return obj


def get_item(table_name: str, key: Dict[str, Union[str, int]]) -> Union[Dict, None]:
    """
    Fetch an item from a DynamoDB table.

    Args:
        table_name (str): The name of the DynamoDB table.
        key (Dict[str, Union[str, int]]): The primary key of the item to fetch.

    Returns:
        Union[Dict, None]: The deserialized item if found, or None if not found.
    """
    try:
        response = ddb_client.get_item(TableName=table_name, Key=key)
        if "Item" in response:
            return {
                k: replace_decimal_with_float(v) for k, v in response["Item"].items()
            }
        return None
    except ClientError as e:
        logger.error(f"Error fetching item from DynamoDB: {e}")
        raise
