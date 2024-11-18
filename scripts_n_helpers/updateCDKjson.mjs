#!/usr/bin/node

import { readFile, writeFile } from 'fs/promises';
import { STSClient, GetCallerIdentityCommand } from "@aws-sdk/client-sts"; 

const client = new STSClient({region:'us-west-2'});
const command = new GetCallerIdentityCommand();
const response = await client.send(command);
let accountId = (response['Account']);

let cdkJson = JSON.parse(await readFile("./cdk.json", "utf8"));
cdkJson['context']['dev']['AwsAccountId'] = accountId;

writeFile("./cdk.json", JSON.stringify(cdkJson, null, 2), "utf8")

