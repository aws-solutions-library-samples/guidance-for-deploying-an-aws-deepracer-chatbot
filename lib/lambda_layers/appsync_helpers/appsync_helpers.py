"""
This module provides utility functions for sending authenticated requests to AWS AppSync API using the Signature Version 4 (SigV4) protocol.
"""

import json
import os
from typing import Any, Dict, Optional, Union

from aws_lambda_powertools import Logger
from boto3.session import Session
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from requests import request

region = os.environ.get("AWS_REGION")
endpoint = os.environ.get("APPSYNC_URL", None)

logger = Logger()


def sigv4_request(
    url: str,
    method: str = "GET",
    body: Optional[bytes] = None,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    service: str = "execute-api",
    region: str = os.environ["AWS_REGION"],
    credentials: Optional[Dict[str, str]] = Session()
    .get_credentials()
    .get_frozen_credentials(),
):
    """Sends an HTTP request signed with SigV4

    Args:
        url (str): The request URL (e.g. 'https://www.example.com').
        method (str, optional): The request method (e.g. 'GET', 'POST', 'PUT', 'DELETE'). Defaults to 'GET'.
        body (bytes, optional): The request body (e.g. json.dumps({ 'foo': 'bar' })). Defaults to None.
        params (Dict[str, str], optional): The request query params (e.g. { 'foo': 'bar' }). Defaults to None.
        headers (Dict[str, str], optional): The request headers (e.g. { 'content-type': 'application/json' }). Defaults to None.
        service (str, optional): The AWS service name. Defaults to 'execute-api'.
        region (str, optional): The AWS region id. Defaults to the env var 'AWS_REGION'.
        credentials (Dict[str, str], optional): The AWS credentials. Defaults to the current boto3 session's credentials.

    Returns:
        requests.Response: The HTTP response
    """

    # sign request
    req = AWSRequest(method=method, url=url, data=body, params=params, headers=headers)
    SigV4Auth(credentials, service, region).add_auth(req)
    req = req.prepare()

    # send request
    return request(method=req.method, url=req.url, headers=req.headers, data=req.body)


def send_mutation(
    query: str,
    variables: Dict[str, Union[str, int, float, bool, None]],
) -> Optional[Dict[str, Any]]:
    """Triggers a mutation on the Appsync API to trigger a subscription

    Args:
        query (str): The GraphQL mutation query.
        variables (Dict[str, Union[str, int, float, bool, None]]): The variables for the mutation query.

    Returns:
        Optional[Dict[str, Any]]: The response from the mutation, or None if an error occurred.
    """

    headers = {"Content-Type": "application/json"}

    payload = {
        "query": query,
        "variables": variables,
    }
    logger.debug(payload)

    try:
        response = sigv4_request(
            url=endpoint,
            method="POST",
            service="appsync",
            body=json.dumps(payload),
            headers=headers,
        ).json()
        logger.debug(f"mutation response: {response}")
        if "errors" in response:
            logger.error(f"Error publishing to AppSync: {response["errors"]}")
            raise Exception("Error publishing to AppSync,  see logs for details")
        else:
            return response
    except Exception as exception:
        logger.exception("Error with Mutation, {exception}")
        raise Exception("Error publishing to AppSync,  see logs for details")
    return None
