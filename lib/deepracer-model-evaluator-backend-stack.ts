import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { CfnOutput, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { IDistribution } from 'aws-cdk-lib/aws-cloudfront';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { LambdaPowertoolsLayer } from 'cdk-aws-lambda-powertools-layer';
import { Construct } from 'constructs';
import { Api } from './api';
import { Authentication } from './authentication';
import { BedrockIntegrationPyResolver } from './bedrock-integration-resolver-py';
import { BuildConfig } from './build-config';
import { LambdaLayers } from './custom_types';
import { ModelStorageAndPreProcessing } from './model_storage';
import path = require('path');


export interface DeepRacerModelEvaluatorBackendStackProps extends StackProps {
  auth: Authentication;
  logsBucket: s3.Bucket;
  webSiteDistribution: IDistribution
}


export class DeepRacerModelEvaluatorBackendStack extends Stack {
  public readonly appsyncApi: Api;

  constructor(scope: Construct, id: string, props: DeepRacerModelEvaluatorBackendStackProps, buildConfig: BuildConfig) {
    super(scope, id, props);

    this.appsyncApi = new Api(this, 'api', {
      userPool: props.auth.userPool
    })

    const noneDataSource = this.appsyncApi.api.addNoneDataSource(`NoneDataSourceV2-${buildConfig.Environment}`)

    const lambdaPowerToolsLayer = new LambdaPowertoolsLayer(this, 'LambdaPowerToolsLayer')

    const appsyncHelpersLayer = new PythonLayerVersion(this, `AppsyncHelpers`, {
      removalPolicy: RemovalPolicy.DESTROY,
      entry: path.join(__dirname, 'lambda_layers/appsync_helpers'),
      compatibleArchitectures: [lambda.Architecture.X86_64, lambda.Architecture.ARM_64],
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12]
    });

    const deepracerTracksLayer = new PythonLayerVersion(this, `DeepRacerTracks`, {
      removalPolicy: RemovalPolicy.DESTROY,
      entry: path.join(__dirname, 'lambda_layers/deepracer_tracks'),
      compatibleArchitectures: [lambda.Architecture.X86_64, lambda.Architecture.ARM_64],
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_12]
    });

    const lambdaLayers: LambdaLayers = {
      appsyncHelpers: appsyncHelpersLayer,
      deepracerTracks: deepracerTracksLayer,
      lambdaPowerTools: lambdaPowerToolsLayer
    }

    // S3 bucket for storing various files, like embeddings for the knowledge bases
    const fileStoreBucket = new s3.Bucket(this, `fileStorage${buildConfig.Environment}`, {
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: props.logsBucket,
      serverAccessLogsPrefix: `access-logs/${id}-bucket/`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    })

    // Resources for uploading, pre-processing and storing users DeepRacer models, makes them available for the user to chat with.
    let modelStorage = new ModelStorageAndPreProcessing(this, 'ModelStorage', {
      api: this.appsyncApi.api,
      apiNoneDataSource: noneDataSource,
      authenticatedUserRole: props.auth.authenticatedUserRole,
      webSiteDistribution: props.webSiteDistribution,
      lambdaLayers: lambdaLayers,
      logsBucket: props.logsBucket,
    })

    // Resources for making it possible to chat with bedrock
    new BedrockIntegrationPyResolver(this, 'BedrockPyResolver', {
      api: this.appsyncApi.api,
      apiNoneDataSource: noneDataSource,
      environment: buildConfig.Environment,
      bedrock_region: buildConfig.BedrockRegion,
      fileStoreBucket: fileStoreBucket,
      modelStorageTable: modelStorage.table,
      lambdaLayers: lambdaLayers
    })

    new CfnOutput(this, "DocumentStore", {
      value: fileStoreBucket.bucketName
    });
  }
}
