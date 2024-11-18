#!/usr/bin/node

import { GetCallerIdentityCommand, STSClient } from "@aws-sdk/client-sts";
import chalk from "chalk";
import { readFile } from "fs/promises";
import terminalLink from "terminal-link";

function randomPassword() {
  const charCode = Math.floor(Math.random() * (47 - 35 + 1)) + 35;
  const password =
    Math.random().toString(36).slice(2) +
    String.fromCharCode(charCode) +
    Math.random().toString(36).toUpperCase().slice(2);
  return password;
}

const password = randomPassword();
const passwordOutput = `Your randomly generated password is: ${chalk.bgBlack(
  chalk.yellow(password)
)}`;

const client = new STSClient({ region: "us-west-2" });
const command = new GetCallerIdentityCommand();
const response = await client.send(command);
let accountId = response["Account"];

let outputs = JSON.parse(await readFile("./outputs.json", "utf8"));

var chatbotUrlOutput = "";
var cognitoCommand1 = "";
var cognitoCommand2 = "";
var cognitoCommand3 = "";

for (const [key, value] of Object.entries(outputs)) {
  if (key.includes("-backend-")) {
    // backend
    // do nothing
  } else if (key.includes("-")) {
    // main
    for (const [innerKey, innerValue] of Object.entries(value)) {
      if (innerKey.startsWith("WebsiteUserInterfaceDomainName")) {
        const link = terminalLink(chalk.blue(innerValue), innerValue);
        chatbotUrlOutput = `DeepRacer Chatbot URL: ${link}`;
      } else if (
        innerKey.startsWith("ExportsOutputRefAuthenticationUserPool")
      ) {
        cognitoCommand1 = `Command to create user: ${chalk.bgBlack(
          chalk.blueBright(
            `aws cognito-idp admin-create-user --user-pool-id ${innerValue} --username ${chalk.redBright(
              "<your email address>"
            )}`
          )
        )}`;
        cognitoCommand2 = `Command to add new user to group: ${chalk.bgBlack(
          chalk.blueBright(
            `aws cognito-idp admin-add-user-to-group --user-pool-id ${innerValue} --group-name Users --username ${chalk.redBright(
              "<your email address>"
            )}`
          )
        )}`;
        cognitoCommand3 = `Command to set user password: ${chalk.bgBlack(
          chalk.blueBright(
            `aws cognito-idp admin-set-user-password --user-pool-id ${innerValue} --permanent --password "${password}" --username ${chalk.redBright(
              "<your email address>"
            )}`
          )
        )}`;
      }
    }
  }
}

// Output
console.log("");
console.log(cognitoCommand1);
console.log(cognitoCommand2);
console.log(cognitoCommand3);
console.log("");
console.log(passwordOutput);
console.log("");
console.log(chatbotUrlOutput);
