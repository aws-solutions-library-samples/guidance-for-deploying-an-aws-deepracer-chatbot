import base64
import json
import os
import re
from typing import BinaryIO, Dict, List, Optional, Union

import boto3
from aws_lambda_powertools import Logger
from utils.utils import is_base64

logger = Logger()


class TitanEmbeddings:
    """
    A class for generating Titan embeddings using the Bedrock runtime.
    """

    accept = "application/json"
    content_type = "application/json"

    def __init__(
        self,
        model_id: str = "amazon.titan-embed-image-v1",
        boto3_client: Optional[boto3.Session.client] = None,
        region_name: Optional[str] = None,
    ):
        """
        Initialize the TitanEmbeddings instance.

        Args:
            model_id (str): The ID of the model to use for generating embeddings.
            boto3_client (boto3.Session.client, optional): An existing Boto3 client instance.
            region_name (str, optional): The AWS region name. If not provided, it will be retrieved from environment variables.
        """
        self.model_id = model_id
        self.bedrock_boto3 = boto3_client or boto3.client(
            service_name="bedrock-runtime",
            region_name=region_name or os.environ.get("AWS_REGION"),
        )

    def __call__(self, body: Dict[str, Union[str, bytes, BinaryIO]]) -> List[float]:
        """
        Generate Titan embeddings for the given input_data.

        Args:
            body (Dict[str, str]]): A dictionary containing 'textInput' and/or 'imageInput' keys.
                'inputText': The text to generate embeddings for.
                'inputImage': The image data as base64-encoded string to generate embeddings for.

        Returns:
            List[float]: The generated embedding.

        Raises:
            ValueError: If neither text nor image is provided in the input_data.
        """
        if not body:
            raise ValueError("Embedding body cannot be empty")

        # Verify that image input is base64, if present
        if "inputImage" in body:
            if isinstance(body["inputImage"], bytes):
                body["inputImage"] = base64.b64encode(body["inputImage"]).decode(
                    "utf-8"
                )
            elif not is_base64(body["inputImage"]):
                raise ValueError(
                    "The provided image input must be a valid base64-encoded string"
                )

        try:
            logger.debug("Calling Embedding model", extra={"body": body})
            response = self.bedrock_boto3.invoke_model(
                body=json.dumps(body),
                modelId=self.model_id,
                accept=self.accept,
                contentType=self.content_type,
            )
            response_body = json.loads(response["body"].read())
            logger.debug("Embedding model response", extra={"body": response_body})
            return response_body["embedding"]
        except Exception as e:
            raise ValueError(f"Error generating embeddings: {str(e)}")
