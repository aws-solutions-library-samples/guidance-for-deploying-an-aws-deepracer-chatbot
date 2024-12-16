import * as cdk from "aws-cdk-lib";
import { CfnOutput, DockerImage } from "aws-cdk-lib";
import * as appsync from "aws-cdk-lib/aws-appsync";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { LambdaLayers } from "../custom_types";
import { StandardLambdaPythonFunction } from "../standard-constructs/standard-lambda-python-function";
import path = require("path");

export interface BedrockIntegrationPyResolverProps {
  api: appsync.GraphqlApi;
  environment: string;
  bedrock_region: string;
  fileStoreBucket: s3.Bucket;
  modelStorageTable: dynamodb.Table;
  lambdaLayers: LambdaLayers;
  apiNoneDataSource: appsync.NoneDataSource;
}

export class BedrockIntegrationPyResolver extends Construct {
  constructor(
    scope: Construct,
    id: string,
    {
      api,
      apiNoneDataSource,
      environment,
      bedrock_region,
      fileStoreBucket,
      modelStorageTable,
      lambdaLayers,
    }: BedrockIntegrationPyResolverProps
  ) {
    super(scope, id);

    const stack = cdk.Stack.of(scope);

    // Create the DynamoDB table with userId as the partition key and sessionId as the sort key
    const session_store_table = new dynamodb.Table(this, "SessionTableV3", {
      partitionKey: { name: "userId", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "sessionId", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: true,
    });

    new CfnOutput(this, "SessionTableV3Tablename", {
      value: session_store_table.tableName,
      description: "Name of the DynamoDB table",
    });

    ///////////////////// Bedrock resources ///////////////////////////////////
    const lambdaFunction = new StandardLambdaPythonFunction(
      this,
      "BedrockIntegrationV2",
      {
        entry: path.join(__dirname, "function"),
        index: "index.py",
        runtime: lambda.Runtime.PYTHON_3_12,
        architecture: lambda.Architecture.X86_64,
        handler: "handler",
        timeout: cdk.Duration.minutes(2),
        memorySize: 2048,
        bundling: {
          image: DockerImage.fromRegistry(
            "public.ecr.aws/sam/build-python3.12:latest-x86_64"
          ),
        },

        environment: {
          APPSYNC_URL: api.graphqlUrl,
          BEDROCK_REGION: bedrock_region,
          CHAT_HISTORY_DDB_TABLE_NAME: session_store_table.tableName,
          MODEL_STORAGE_DDB_TABLE_NAME: modelStorageTable.tableName,
          POWERTOOLS_SERVICE_NAME: "BedrockIntegrationV2",
          POWERTOOLS_LOG_LEVEL: "INFO",
        },
        layers: [
          lambdaLayers.appsyncHelpers,
          lambdaLayers.lambdaPowerTools,
          lambdaLayers.deepracerTracks,
        ],
      }
    );
    session_store_table.grantReadWriteData(lambdaFunction);
    api.grantMutation(lambdaFunction, "streamResponse");
    fileStoreBucket.grantRead(lambdaFunction);

    lambdaFunction.addToRolePolicy(
      new PolicyStatement({
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-image-v1",
        ],
      })
    );

    modelStorageTable.grantReadData(lambdaFunction);

    const bedrockLambdaDataSource = new appsync.LambdaDataSource(
      this,
      `BedrockDataSource${environment}`,
      {
        api: api,
        lambdaFunction: lambdaFunction,
      }
    );

    bedrockLambdaDataSource.createResolver("sendMessageResolver", {
      typeName: "Mutation",
      fieldName: "sendMessage",
      requestMappingTemplate: appsync.MappingTemplate.fromString(
        `{
            "version": "2017-02-28",
            "operation": "Invoke",
            "invocationType": "Event",
            "payload": {
              "arguments": $utils.toJson($context.arguments),
              "identity": $utils.toJson($context.identity),
              "info": {
                  "fieldName": $utils.toJson($context.info.fieldName),
                  "parentTypeName": $utils.toJson($context.info.parentTypeName),
                  "selectionSetList": $utils.toJson($context.info.selectionSetList),
                  "variables": $utils.toJson($context.info.variables)
              }
          }
        }`
      ),
      responseMappingTemplate: appsync.MappingTemplate.fromString(
        "$util.toJson($context.result)"
      ),
    });

    // only allow a user to subscribe to it´s own conversation
    apiNoneDataSource.createResolver(
      `MutationStreamResponseResolver${environment}`,
      {
        typeName: "Mutation",
        fieldName: "streamResponse",
        requestMappingTemplate: appsync.MappingTemplate.fromString(
          `{
                    "version": "2017-02-28",
                    "payload": $util.toJson($context.args)
                }`
        ),
        responseMappingTemplate: appsync.MappingTemplate.fromString(
          "$util.toJson($context.result)"
        ),
      }
    );

    const subscriptionPermissions = `
            #if($context.identity.sub == $context.args.userId)
                {
                "version": "2018-05-29",
                "payload": $util.toJson($context.args)
            }
            #else
                $utils.unauthorized()
            #end
            `;
    apiNoneDataSource.createResolver(`onStreamResponseResolver${environment}`, {
      typeName: "Subscription",
      fieldName: "onStreamResponse",
      requestMappingTemplate: appsync.MappingTemplate.fromString(
        subscriptionPermissions
      ),
      responseMappingTemplate: appsync.MappingTemplate.fromString(
        "$util.toJson($context.result)"
      ),
    });
  }
}
