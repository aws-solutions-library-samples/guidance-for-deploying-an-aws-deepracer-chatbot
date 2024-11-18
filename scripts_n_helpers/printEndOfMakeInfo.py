#!/usr/bin/env python3

import json
import random
import string
import boto3
from termcolor import colored
import os
import argparse
import subprocess
import time

def random_password():
    # Generate random character code between 35 and 47
    char_code = random.randint(35, 47)
    # Create random strings using ascii letters and digits
    part1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return part1 + chr(char_code) + part2

def execute_command(cmd, description):
    print(f"\nExecuting: {description}")
    try:
        if isinstance(cmd, list):
            result = subprocess.run(cmd, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode == 0:
            print(colored("Success!", "green"))
            return True
        else:
            print(colored(f"Error: {result.stderr}", "red"))
            return False
    except Exception as e:
        print(colored(f"Error executing command: {e}", "red"))
        return False

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
        # backend - do nothing
        continue
    elif "-" in key:
        # main
        for inner_key, inner_value in value.items():
            if inner_key.startswith("WebsiteUserInterfaceDomainName"):
                chatbot_url_output = f"DeepRacer Chatbot URL: {colored(inner_value, 'blue')}"
            elif inner_key.startswith("ExportsOutputRefAuthenticationUserPool"):
                # Create the command strings with the actual email address
                create_user_cmd = f'aws cognito-idp admin-create-user --user-pool-id {inner_value} --username {email_address}'
                add_to_group_cmd = f'aws cognito-idp admin-add-user-to-group --user-pool-id {inner_value} --group-name Users --username {email_address}'
                
                # Handle set-password command as a list to properly handle the password string
                set_password_cmd = [
                    'aws', 'cognito-idp', 'admin-set-user-password',
                    '--user-pool-id', inner_value,
                    '--username', email_address,
                    '--password', password,
                    '--permanent'
                ]

                # Execute the commands in sequence
                print("\nStarting user creation process...")
                
                if execute_command(create_user_cmd, "Creating user"):
                    # Wait a moment for the user to be created
                    time.sleep(2)
                    
                    if execute_command(add_to_group_cmd, "Adding user to group"):
                        time.sleep(1)
                        
                        if execute_command(set_password_cmd, "Setting user password"):
                            print('')
                            print(password_output)

                else:
                    print(colored("✗ Failed to create user", "red"))

print()
# print(chatbot_url_output)
