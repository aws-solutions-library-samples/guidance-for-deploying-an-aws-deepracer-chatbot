import * as cdk from "aws-cdk-lib";
import * as appsync from "aws-cdk-lib/aws-appsync";
import * as cognito from "aws-cdk-lib/aws-cognito";
import { RetentionDays } from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import path = require("path");

export interface ApiProps {
  userPool: cognito.IUserPool;
}

export class Api extends Construct {
  public readonly api: appsync.GraphqlApi;

  constructor(scope: Construct, id: string, { userPool }: ApiProps) {
    super(scope, id);

    const stack = cdk.Stack.of(scope);

    const api = new appsync.GraphqlApi(this, "graphQlApi", {
      name: `api-${stack.stackName}`,
      definition: appsync.Definition.fromFile(
        path.join(__dirname, "schema.graphql")
      ),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.USER_POOL,
          userPoolConfig: {
            userPool,
          },
        },
        additionalAuthorizationModes: [
          {
            authorizationType: appsync.AuthorizationType.IAM,
          },
        ],
      },
      xrayEnabled: true,
      logConfig: {
        retention: RetentionDays.ONE_WEEK,
      },
    });
    this.api = api;

    new cdk.CfnOutput(this, "aws_appsync_graphqlEndpoint", {
      value: api.graphqlUrl,
    });
  }
}
