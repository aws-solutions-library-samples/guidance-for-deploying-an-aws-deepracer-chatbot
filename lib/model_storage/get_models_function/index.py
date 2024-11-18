import os

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from boto3.dynamodb.conditions import Key

logger = Logger()
app = AppSyncResolver()

DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
ddbTable = dynamodb.Table(DDB_TABLE_NAME)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def handler(event, context):
    response = app.resolve(event, context)
    return response


@app.resolver(type_name="Query", field_name="getModels")
def getModels():

    identity = app.current_event.get("identity")
    user_id = identity.get("sub")

    try:
        response = ddbTable.query(KeyConditionExpression=Key("userId").eq(user_id))
        logger.info(f"Get models DDB response", extra={"body": response})
        if "Items" not in response:
            return []
        items = response["Items"]
        logger.info(f"Items", extra={"body": items})
        return items
    except Exception as e:
        logger.exception(e)
        return []
