import { CfnOutput, Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { IDistribution } from 'aws-cdk-lib/aws-cloudfront';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';
import { Authentication } from './authentication';
import { BuildConfig } from './build-config';
import { Website } from './website';

export class DeepRacerModelEvaluatorMainStack extends Stack {
  public readonly auth: Authentication;
  public readonly logsBucket: s3.Bucket;
  public readonly websiteDistribution:IDistribution;

  constructor(scope: Construct, id: string, props: StackProps, buildConfig: BuildConfig) {
    super(scope, id, props);

    const stack = Stack.of(this);

    const logsBucket = new s3.Bucket(this, 'logsBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsPrefix: 'access-logs/logsBucket/',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      autoDeleteObjects: true,
      objectOwnership: s3.ObjectOwnership.OBJECT_WRITER,
      removalPolicy: RemovalPolicy.DESTROY,
      lifecycleRules: [{ expiration: Duration.days(30) }, { abortIncompleteMultipartUploadAfter: Duration.days(1) }],
    });
    this.logsBucket = logsBucket;
    logsBucket.policy?.document.addStatements(
      new iam.PolicyStatement({
        sid: 'AllowSSLRequestsOnly',
        effect: iam.Effect.DENY,
        principals: [new iam.AnyPrincipal()],
        actions: ['s3:*'],
        resources: [logsBucket.bucketArn, logsBucket.bucketArn + '/*'],
        conditions: { NumericLessThan: { 's3:TlsVersion': '1.2' } },
      })
    );

    const website = new Website(this, 'Website', {
      logsBucket: this.logsBucket,
    });
    this.websiteDistribution = website.distribution;

    this.auth = new Authentication(this, 'Authentication', {
      distribution: website.distribution
    });

    new CfnOutput(this, "region", {
      value: stack.region
    });
  }
}
