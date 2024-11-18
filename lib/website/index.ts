import * as cdk from "aws-cdk-lib";
import { Stack } from "aws-cdk-lib";
import * as cf from "aws-cdk-lib/aws-cloudfront";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export interface WebsiteProps {
  logsBucket: s3.Bucket;
}
export class Website extends Construct {
  public readonly distribution: cloudfront.IDistribution;
  public readonly bucket: s3.IBucket;

  constructor(scope: Construct, id: string, props: WebsiteProps) {
    super(scope, id);

    const stack = Stack.of(this);

    this.bucket = new s3.Bucket(this, "WebsiteBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      serverAccessLogsBucket: props.logsBucket,
      serverAccessLogsPrefix: `access-logs/${id}-bucket/`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    this.bucket.policy?.document.addStatements(
      new iam.PolicyStatement({
        sid: "AllowSSLRequestsOnly",
        effect: iam.Effect.DENY,
        principals: [new iam.AnyPrincipal()],
        actions: ["s3:*"],
        resources: [this.bucket.bucketArn, this.bucket.bucketArn + "/*"],
        conditions: { NumericLessThan: { "s3:TlsVersion": "1.2" } },
      })
    );

    const originAccessIdentity = new cf.OriginAccessIdentity(this, "S3OAI");
    this.bucket.grantRead(originAccessIdentity);

    this.distribution = new cf.CloudFrontWebDistribution(this, "Distribution", {
      viewerProtocolPolicy: cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      priceClass: cf.PriceClass.PRICE_CLASS_100,
      httpVersion: cf.HttpVersion.HTTP2_AND_3,
      loggingConfig: {
        bucket: props.logsBucket,
        includeCookies: false,
        prefix: "access-logs/cf_distribution/",
      },
      originConfigs: [
        {
          behaviors: [{ isDefaultBehavior: true }],
          s3OriginSource: {
            s3BucketSource: this.bucket,
            originAccessIdentity,
          },
        },
      ],
      errorConfigurations: [
        {
          errorCode: 404,
          errorCachingMinTtl: 0,
          responseCode: 200,
          responsePagePath: "/index.html",
        },
      ],
    });

    // ###################################################
    // Outputs
    // ###################################################
    new cdk.CfnOutput(this, "UserInterfaceDomainName", {
      value: `https://${this.distribution.distributionDomainName}`,
    });
    new cdk.CfnOutput(this, "UserInterfaceBucketName", {
      value: this.bucket.bucketName,
    });
    new cdk.CfnOutput(this, "UserInterfaceDistributionId", {
      value: this.distribution.distributionId,
    });
  }
}
