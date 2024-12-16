#!/usr/bin/env node

import { 
  STSClient, 
  GetCallerIdentityCommand 
} from "@aws-sdk/client-sts";
import { 
  CognitoIdentityProviderClient, 
  AdminCreateUserCommand,
  AdminAddUserToGroupCommand,
  AdminSetUserPasswordCommand,
  UsernameExistsException
} from "@aws-sdk/client-cognito-identity-provider";
import { promises as fs } from 'fs';
import chalk from 'chalk';
import readline from 'readline';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('email', {
      alias: 'e',
      description: 'Email address for the user',
      type: 'string'
  })
  .parse();

function generateRandomPassword() {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const numbers = '0123456789';
  const specialChars = '#$%&()*+,-./';

  const generatePart = (chars, length) => {
      let result = '';
      for (let i = 0; i < length; i++) {
          result += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      return result;
  };

  const part1 = generatePart(lowercase + numbers, 8);
  const part2 = generatePart(uppercase + numbers, 8);
  const specialChar = specialChars.charAt(Math.floor(Math.random() * specialChars.length));

  return part1 + specialChar + part2;
}

async function getUserInput(prompt) {
  const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
  });

  return new Promise(resolve => {
      rl.question(prompt, (answer) => {
          rl.close();
          resolve(answer.trim());
      });
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  // Get email address
  const emailAddress = argv.email || await getUserInput("Please enter your email address: ");

  // Generate password
  const password = generateRandomPassword();
  const passwordOutput = `Your randomly generated password is: ${chalk.yellow(password)}`;

  // Initialize AWS clients
  const region = 'us-west-2';
  const stsClient = new STSClient({ region });
  const cognitoClient = new CognitoIdentityProviderClient({ region });

  try {
      // Get AWS account ID
      const stsResponse = await stsClient.send(new GetCallerIdentityCommand({}));
      const accountId = stsResponse.Account;

      // Read outputs file
      const outputs = JSON.parse(await fs.readFile('./outputs.json', 'utf8'));

      for (const [key, value] of Object.entries(outputs)) {
          if (key.includes("-backend-")) continue;
          if (key.includes("-")) {
              for (const [innerKey, innerValue] of Object.entries(value)) {
                  if (innerKey.startsWith("WebsiteUserInterfaceDomainName")) {
                      console.log(`DeepRacer Chatbot URL: ${chalk.blue(innerValue)}`);
                  } else if (innerKey.startsWith("ExportsOutputRefAuthenticationUserPool")) {
                      const userPoolId = innerValue;

                      console.log("\nStarting user creation process...");

                      // Step 1: Create user
                      console.log("\nExecuting: Creating user");
                      try {
                          await cognitoClient.send(new AdminCreateUserCommand({
                              UserPoolId: userPoolId,
                              Username: emailAddress,
                              MessageAction: 'SUPPRESS'
                          }));
                          console.log(chalk.green("Success!"));
                      } catch (error) {
                          if (error instanceof UsernameExistsException) {
                              console.log(chalk.yellow("Note: User already exists"));
                          } else {
                              console.log(chalk.red(`✗ Error creating user: ${error.message}`));
                              process.exit(1);
                          }
                      }

                      await sleep(2000);

                      // Step 2: Add user to group
                      console.log("\nExecuting: Adding user to group");
                      try {
                          await cognitoClient.send(new AdminAddUserToGroupCommand({
                              UserPoolId: userPoolId,
                              Username: emailAddress,
                              GroupName: 'Users'
                          }));
                          console.log(chalk.green("Success!"));
                      } catch (error) {
                          console.log(chalk.red(`✗ Error adding user to group: ${error.message}`));
                          process.exit(1);
                      }

                      await sleep(1000);

                      // Step 3: Set permanent password
                      console.log("\nExecuting: Setting user password");
                      try {
                          await cognitoClient.send(new AdminSetUserPasswordCommand({
                              UserPoolId: userPoolId,
                              Username: emailAddress,
                              Password: password,
                              Permanent: true
                          }));
                          console.log(chalk.green("Success!"));
                          console.log('');
                          console.log(passwordOutput);
                      } catch (error) {
                          console.log(chalk.red(`✗ Error setting password: ${error.message}`));
                          process.exit(1);
                      }
                  }
              }
          }
      }
  } catch (error) {
      console.error(chalk.red(`Error: ${error.message}`));
      process.exit(1);
  }
}

main().catch(error => {
  console.error(chalk.red(`Unhandled error: ${error.message}`));
  process.exit(1);
});
