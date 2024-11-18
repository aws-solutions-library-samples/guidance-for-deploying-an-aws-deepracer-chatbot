import * as cognitoIdentityPool from "@aws-cdk/aws-cognito-identitypool-alpha";
import * as cdk from "aws-cdk-lib";
import * as cf from "aws-cdk-lib/aws-cloudfront";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";
import * as path from "node:path";

export interface UserInterfaceProps {
  readonly appsyncGraphqlEndpoint: string;
  readonly userPoolId: string;
  readonly userPoolClientId: string;
  readonly identityPool: cognitoIdentityPool.IdentityPool;
  readonly distribution: cf.IDistribution;
  readonly websiteBucket: cdk.aws_s3.IBucket;
}

export class UserInterface extends Construct {
  constructor(scope: Construct, id: string, props: UserInterfaceProps) {
    super(scope, id);

    const appPath = path.join(__dirname, "nextjs-app");

    new s3deploy.BucketDeployment(this, "UserInterfaceDeployment", {
      sources: [s3deploy.Source.asset(path.join(__dirname, "nextjs-app/out"))],
      destinationBucket: props.websiteBucket,
      distribution: props.distribution,
    });

    // ###################################################
    // Outputs
    // ###################################################
    new cdk.CfnOutput(this, "UserInterfaceDomainName", {
      value: `https://${props.distribution.distributionDomainName}`,
    });
  }
}
