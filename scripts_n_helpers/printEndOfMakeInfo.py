#!/usr/bin/env python3

import json
import random
import string
import boto3
from termcolor import colored
import os
import argparse
import time

def random_password():
    char_code = random.randint(35, 47)
    part1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return part1 + chr(char_code) + part2

# Set up command line argument parsing
parser = argparse.ArgumentParser(description='Generate Cognito user commands')
parser.add_argument('-e', '--email', help='Email address for the user')
args = parser.parse_args()

# Use command line email if provided, otherwise prompt
email_address = args.email if args.email else input("Please enter your email address: ").strip()

# Generate password
password = random_password()
password_output = f"Your randomly generated password is: {colored(password, 'yellow', 'on_black')}"

# Get AWS account ID
sts_client = boto3.client('sts', region_name='us-west-2')
account_id = sts_client.get_caller_identity()['Account']

# Read outputs file
with open('./outputs.json', 'r') as file:
    outputs = json.load(file)

chatbot_url_output = ""

# Process outputs
for key, value in outputs.items():
    if "-backend-" in key:
        continue
    elif "-" in key:
        for inner_key, inner_value in value.items():
            if inner_key.startswith("WebsiteUserInterfaceDomainName"):
                chatbot_url_output = f"DeepRacer Chatbot URL: {colored(inner_value, 'blue')}"
                print(chatbot_url_output)
            elif inner_key.startswith("ExportsOutputRefAuthenticationUserPool"):
                user_pool_id = inner_value
                cognito_client = boto3.client('cognito-idp', region_name='us-west-2')
                
                print("\nStarting user creation process...")
                
                # Step 1: Create user
                print("\nExecuting: Creating user")
                try:
                    cognito_client.admin_create_user(
                        UserPoolId=user_pool_id,
                        Username=email_address,
                        MessageAction='SUPPRESS'  # Suppress sending the temporary password
                    )
                    print(colored("Success!", "green"))
                except cognito_client.exceptions.UsernameExistsException:
                    print(colored("Note: User already exists", "yellow"))
                except Exception as e:
                    print(colored(f"✗ Error creating user: {str(e)}", "red"))
                    exit(1)  # Exit if we can't create/verify user
                
                time.sleep(2)  # Wait for user creation to propagate
                
                # Step 2: Add user to group
                print("\nExecuting: Adding user to group")
                try:
                    cognito_client.admin_add_user_to_group(
                        UserPoolId=user_pool_id,
                        Username=email_address,
                        GroupName='Users'
                    )
                    print(colored("Success!", "green"))
                except Exception as e:
                    print(colored(f"✗ Error adding user to group: {str(e)}", "red"))
                    exit(1)  # Exit if we can't add to group
                
                time.sleep(1)
                
                # Step 3: Set permanent password
                print("\nExecuting: Setting user password")
                try:
                    cognito_client.admin_set_user_password(
                        UserPoolId=user_pool_id,
                        Username=email_address,
                        Password=password,
                        Permanent=True
                    )
                    print(colored("Success!", "green"))
                    print('')
                    print(password_output)
                except Exception as e:
                    print(colored(f"✗ Error setting password: {str(e)}", "red"))
                    exit(1)  # Exit if we can't set password

print()
