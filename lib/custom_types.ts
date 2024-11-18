import * as lambda from 'aws-cdk-lib/aws-lambda';

export type LambdaLayers = {
    appsyncHelpers: lambda.LayerVersion,
    lambdaPowerTools: lambda.LayerVersion
  }