import os

import boto3

USERS_GROUP_NAME = os.environ["USERS_GROUP_NAME"]

cognito_client = boto3.client("cognito-idp")


def lambda_handler(event: dict, context) -> str:
    print(event)
    try:
        response = cognito_client.admin_add_user_to_group(
            UserPoolId=event.get("userPoolId"),
            Username=event.get("userName"),
            GroupName=USERS_GROUP_NAME,
        )
        print(f"User {event.get('userName')} added to group {USERS_GROUP_NAME}")
        return event
    except Exception as e:
        print(f"Error adding user to group: {e}")
        raise e
