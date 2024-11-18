import os
import urllib.parse

import appsync_helpers
import boto3
import file_utils
from aws_lambda_powertools import Logger
from model_parser import parse_model
from model_storage import ModelStorage

logger = Logger()

s3_client = boto3.client("s3")

DDB_TABLE_NAME = os.environ["DDB_TABLE_NAME"]
model_storage = ModelStorage(ddb_table_name=DDB_TABLE_NAME)


class InvalidFileTypeError(Exception):
    """Raised when the file type is not supported."""

    pass


def send_mutation(userId, modelName, status, statusDetails):
    query = """
    mutation ModelAdded(
        $userId: ID!
        $modelName: String!
        $status: ModelStatus!
        $statusDetails: String
        ) {
            modelAdded(
                userId: $userId
                modelName: $modelName
                status: $status
                statusDetails: $statusDetails
            ) {
                models {
                    modelName
                    status
                    statusDetails
                    __typename
                    }
                    userId
                    __typename
            }
        }
    """

    variables = {
        "userId": userId,
        "modelName": modelName,
        "status": status,
        "statusDetails": statusDetails,
    }
    logger.debug("Sending mutation", extra={"body": query, "variables": variables})
    response = appsync_helpers.send_mutation(
        query,
        variables,
    )
    logger.debug(f"Mutation response", extra={"body": response, "variables": variables})


def handler(event, context):
    for record in event["Records"]:
        bucket_name = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        userSub = file_utils.extract_sub_from_s3_key(key)

        status = "ready"
        statusDetails = "Model parsed successfully"
        model_data = {}
        try:
            model_name, file_extension = file_utils.extract_model_name_from_path(key)
            local_model_file_path = file_utils.download_model_from_s3(bucket_name, key)
            try:
                extracted_model_path = file_utils.extract_model(
                    local_model_file_path, file_extension
                )
                model_data = parse_model(extracted_model_path)
                status = "ready"
                model_data["status"] = status
            except InvalidFileTypeError as e:
                logger.error("Invalid file type", extra={"body": e})
                status = "error"
                model_data["status"] = status
                statusDetails = model_data["statusDetails"] = (
                    "Invalid file type, .zip & .tar.gz are the only supported formats."
                )
            except Exception as e:
                logger.error("Could not parse model", extra={"body": e})
                status = "error"
                model_data["status"] = status
                statusDetails = model_data["statusDetails"] = (
                    "Could not parse model, verify that you uploaded an exported DeepRacer model, see the help panel for more details."
                )
        except Exception as e:
            logger.exception(e)
            status = "error"
            model_data["status"] = status
            statusDetails = model_data["statusDetails"] = (
                "An error occurred while parsing the model, please delete the model and try again."
            )
        finally:
            model_storage.add_model(userSub, model_name, model_data)
            file_utils.delete_model_from_s3(bucket_name, key)
            file_utils.delete_model_from_tmp(local_model_file_path)
            send_mutation(userSub, model_name, status, statusDetails)
