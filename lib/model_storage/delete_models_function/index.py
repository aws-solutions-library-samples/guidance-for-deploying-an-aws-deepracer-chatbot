import os

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger()
app = AppSyncResolver()

DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]
dynamodb = boto3.resource("dynamodb")
ddbTable = dynamodb.Table(DDB_TABLE_NAME)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def handler(event, context):
    response = app.resolve(event, context)
    return response


@app.resolver(type_name="Mutation", field_name="deleteModels")
def deleteModels(modelNames: list[str]):
    logger.info(f"Models to delete", extra={"body": modelNames})

    identity = app.current_event.get("identity")
    user_id = identity.get("sub")

    try:
        # Create a batch writer object
        with ddbTable.batch_writer() as batch:
            # Add items to be deleted to the batch
            for model_name in modelNames:
                key = {"userId": user_id, "modelName": model_name}
                response = batch.delete_item(Key=key)
                logger.info(
                    f"Deleted model in DDB", extra={"body": response, "key": key}
                )
        models = []
        for model_name in modelNames:
            models.append({"modelName": model_name, "status": "deleted"})

        return_message = {"userId": user_id, "models": models}
        logger.info(f"return_message", extra={"body": return_message})
        return return_message
    except Exception as e:
        logger.error(e)
        return []
