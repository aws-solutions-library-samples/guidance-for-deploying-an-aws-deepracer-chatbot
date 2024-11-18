#!/usr/bin / env node
import * as cdk from "aws-cdk-lib";
import { BuildConfig } from "../lib/build-config";
import { DeepRacerModelEvaluatorBackendStack } from "../lib/deepracer-model-evaluator-backend-stack";
import { DeepRacerModelEvaluatorMainStack } from "../lib/deepracer-model-evaluator-main-stack";

function ensureString(
  object: { [name: string]: any },
  propName: string
): string {
  if (!object[propName] || object[propName].trim().length === 0)
    throw new Error(propName + " does not exist or is empty");

  return object[propName];
}

function getConfig() {
  let env = app.node.tryGetContext("config");
  if (!env)
    throw new Error(
      "Context variable missing on CDK command. Pass in as `-c config=XXX`"
    );

  let unparsedEnv = app.node.tryGetContext(env);

  let buildConfig: BuildConfig = {
    AwsAccountId: ensureString(unparsedEnv, "AwsAccountId"),
    AwsRegion: ensureString(unparsedEnv, "AwsRegion"),
    BedrockRegion: ensureString(unparsedEnv, "BedrockRegion"),
    AppName: ensureString(unparsedEnv, "AppName"),
    Environment: ensureString(unparsedEnv, "Environment"),
  };

  return buildConfig;
}

const app = new cdk.App();

const buildConfig: BuildConfig = getConfig();
const env: cdk.Environment = {
  region: buildConfig.AwsRegion,
  account: buildConfig.AwsAccountId,
};

// Main/Base Stack
const mainStackName = buildConfig.AppName + "-" + buildConfig.Environment;
const mainStack = new DeepRacerModelEvaluatorMainStack(
  app,
  mainStackName,
  {
    env: env,
    description: "Guidance for AWS DeepRacer Chatbot (SOXXXXash)", // TODO add guidance number
  },
  buildConfig
);

let mainOnly = app.node.tryGetContext("main_only");
if (mainOnly === "true") {
  console.info("Skipping backend stack creation");
} else {
  // Backend Stack
  const backendStackName =
    buildConfig.AppName + "-backend-" + buildConfig.Environment;
  new DeepRacerModelEvaluatorBackendStack(
    app,
    backendStackName,
    {
      auth: mainStack.auth,
      logsBucket: mainStack.logsBucket,
      webSiteDistribution: mainStack.websiteDistribution,
      env: env,
      description: "Guidance for AWS DeepRacer Chatbot (SOXXXXash)", // TODO add guidance number
    },
    buildConfig
  );
}
