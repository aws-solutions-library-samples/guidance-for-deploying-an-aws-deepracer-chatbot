import * as cdk from "aws-cdk-lib";
import * as appsync from "aws-cdk-lib/aws-appsync";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { LambdaLayers } from "../custom_types";
import { StandardLambdaPythonFunction } from "../standard-constructs/standard-lambda-python-function";
import path = require("path");

export interface ModelStorageAndPreProcessingProps {
  api: appsync.GraphqlApi;
  webSiteDistribution: cdk.aws_cloudfront.IDistribution;
  authenticatedUserRole: iam.IRole;
  lambdaLayers: LambdaLayers;
  apiNoneDataSource: appsync.NoneDataSource;
  logsBucket: s3.Bucket;
}

export class ModelStorageAndPreProcessing extends Construct {
  public readonly table: dynamodb.Table;

  constructor(
    scope: Construct,
    id: string,
    props: ModelStorageAndPreProcessingProps
  ) {
    super(scope, id);

    const stack = cdk.Stack.of(scope);

    const modelBucket = new s3.Bucket(this, "ModelBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: props.logsBucket,
      serverAccessLogsPrefix: `access-logs/${id}-bucket/`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const corsRule = {
      allowedHeaders: [
        "Authorization",
        "Content-Type",
        "X-Amz-Content-Sha256",
        "X-Amz-Date",
        "X-Amz-Security-Token",
        "X-Amz-User-Agent",
      ],
      allowedMethods: [
        s3.HttpMethods.PUT,
        s3.HttpMethods.POST,
        s3.HttpMethods.GET,
        s3.HttpMethods.HEAD,
      ],
      allowedOrigins: [
        "http://localhost:3000",
        "https://" + props.webSiteDistribution.distributionDomainName,
      ],
      exposedHeaders: [
        "x-amz-server-side-encryption",
        "x-amz-request-id",
        "x-amz-id-2",
        "ETag",
      ],
      maxAge: 3000,
    };
    modelBucket.addCorsRule(corsRule);

    new cdk.CfnOutput(this, "ModelBucketName", {
      value: modelBucket.bucketName,
    });

    // logged in user can only read/write their own bucket
    const ownModelsPolicy = new iam.Policy(this, "userAccessToOwnModels", {
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["s3:GetObject", "s3:PutObject", "s3:PutObjectTagging"],
          resources: [
            modelBucket.bucketArn +
              "/private/${cognito-identity.amazonaws.com:sub}",
            modelBucket.bucketArn +
              "/private/${cognito-identity.amazonaws.com:sub}/*",
          ],
        }),
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["s3:ListBucket"],
          resources: [modelBucket.bucketArn],
          conditions: {
            StringLike: {
              "s3:prefix": ["private/${cognito-identity.amazonaws.com:sub}/*"],
            },
          },
        }),
      ],
    });
    ownModelsPolicy.attachToRole(props.authenticatedUserRole);

    // Create the DynamoDB table with userId as the partition key and sessionId as the sort key
    const model_storage_table = new dynamodb.Table(this, "ModelStorage", {
      partitionKey: { name: "userId", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "modelName", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: true,
    });
    this.table = model_storage_table;

    // Lambda function for parsing logs
    const ModelParserLambdaFunction = new StandardLambdaPythonFunction(
      this,
      "ModelParserLambdaFunction",
      {
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_12,
        handler: "handler",
        entry: path.join(__dirname, "model_parser_function"),
        environment: {
          DDB_TABLE_NAME: model_storage_table.tableName,
          APPSYNC_URL: props.api.graphqlUrl,
          POWERTOOLS_SERVICE_NAME: "ModelParserLambdaFunction",
        },
        timeout: cdk.Duration.seconds(120),
        memorySize: 512,
        ephemeralStorageSize: cdk.Size.gibibytes(2),
        layers: [
          props.lambdaLayers.appsyncHelpers,
          props.lambdaLayers.lambdaPowerTools,
        ],
      }
    );

    // Trigger the lambda on new objects in the S3 bucket
    modelBucket.addEventNotification(
      cdk.aws_s3.EventType.OBJECT_CREATED,
      new cdk.aws_s3_notifications.LambdaDestination(ModelParserLambdaFunction)
    );

    props.api.grantMutation(ModelParserLambdaFunction, "modelAdded");
    model_storage_table.grantReadWriteData(ModelParserLambdaFunction);
    modelBucket.grantReadWrite(ModelParserLambdaFunction);

    new cdk.CfnOutput(this, "DdbTableName", {
      value: model_storage_table.tableName,
    });

    // only allow a user to subscribe to it´s own conversation
    props.apiNoneDataSource.createResolver(`modelAddedResolver`, {
      typeName: "Mutation",
      fieldName: "modelAdded",
      requestMappingTemplate: appsync.MappingTemplate.fromString(
        `{
              "version": "2017-02-28",
              "payload": $util.toJson({"userId": $context.args.userId, "models": [{"modelName": $context.args.modelName, "status": $context.args.status, "statusDetails":$context.args.statusDetails }]} )
          }`
      ),
      responseMappingTemplate: appsync.MappingTemplate.fromString(
        "$util.toJson($context.result)"
      ),
    });

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
    props.apiNoneDataSource.createResolver(`onModelAddedResolver`, {
      typeName: "Subscription",
      fieldName: "onModelAdded",
      requestMappingTemplate: appsync.MappingTemplate.fromString(
        subscriptionPermissions
      ),
      responseMappingTemplate: appsync.MappingTemplate.fromString(
        "$util.toJson($context.result)"
      ),
    });

    // API Lambda function for getting all models for a user
    const getModelsApiLambdaFunction = new StandardLambdaPythonFunction(
      this,
      "getModelsApiLambdaFunction",
      {
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_12,
        handler: "handler",
        entry: path.join(__dirname, "get_models_function"),
        environment: {
          DDB_TABLE_NAME: model_storage_table.tableName,
          POWERTOOLS_SERVICE_NAME: "getModelsApiLambdaFunction",
        },
        timeout: cdk.Duration.seconds(120),
        memorySize: 512,
        ephemeralStorageSize: cdk.Size.gibibytes(2),
        layers: [props.lambdaLayers.lambdaPowerTools],
      }
    );

    model_storage_table.grantReadData(getModelsApiLambdaFunction);
    const getModelsDataSource = new appsync.LambdaDataSource(
      this,
      `getModelsApiDataSourceV2`,
      {
        api: props.api,
        lambdaFunction: getModelsApiLambdaFunction,
      }
    );
    getModelsDataSource.createResolver(`getModelsResolver`, {
      typeName: "Query",
      fieldName: "getModels",
    });

    //API Lambda function for deleting user selected models
    const deleteModelsApiLambdaFunction = new StandardLambdaPythonFunction(
      this,
      "deleteModelsApiLambdaFunction",
      {
        runtime: cdk.aws_lambda.Runtime.PYTHON_3_12,
        handler: "handler",
        entry: path.join(__dirname, "delete_models_function"),
        environment: {
          DDB_TABLE_NAME: model_storage_table.tableName,
          POWERTOOLS_SERVICE_NAME: "deleteModelsApiLambdaFunction",
        },
        timeout: cdk.Duration.seconds(120),
        memorySize: 512,
        ephemeralStorageSize: cdk.Size.gibibytes(2),
        layers: [
          props.lambdaLayers.appsyncHelpers,
          props.lambdaLayers.lambdaPowerTools,
        ],
      }
    );
    model_storage_table.grantWriteData(deleteModelsApiLambdaFunction);

    const deleteModelsDataSource = new appsync.LambdaDataSource(
      this,
      `deleteModelsApiDataSource`,
      {
        api: props.api,
        lambdaFunction: deleteModelsApiLambdaFunction,
      }
    );
    deleteModelsDataSource.createResolver(`deleteModelsResolver`, {
      typeName: "Mutation",
      fieldName: "deleteModels",
    });
  }
}
