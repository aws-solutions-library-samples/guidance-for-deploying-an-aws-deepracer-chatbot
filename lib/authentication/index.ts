import * as cognitoIdentityPool from "@aws-cdk/aws-cognito-identitypool-alpha";
import * as cdk from "aws-cdk-lib";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as cognito from "aws-cdk-lib/aws-cognito";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import * as path from "path";
import { StandardLambdaPythonFunction } from "../standard-constructs/standard-lambda-python-function";

export interface AuthenticationProps {
  distribution: cloudfront.IDistribution;
}

export class Authentication extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;
  public readonly identityPool: cognitoIdentityPool.IdentityPool;
  public readonly authenticatedUserRole: iam.IRole;

  constructor(scope: Construct, id: string, props: AuthenticationProps) {
    super(scope, id);

    // Triggers
    const post_confirmation_lambda = new StandardLambdaPythonFunction(
      this,
      "PostConfirmation",
      {
        entry: path.resolve(__dirname, "function"), // Define the entry path relative to the current directory
        runtime: lambda.Runtime.PYTHON_3_12,
        environment: {
          USERS_GROUP_NAME: "Users",
          POWERTOOLS_SERVICE_NAME: "PostConfirmation",
        },
      }
    );

    const userPool = new cognito.UserPool(this, "UserPool", {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      enableSmsRole: false,
      selfSignUpEnabled: false,
      autoVerify: { email: true, phone: false },
      signInAliases: {
        email: true,
      },
      mfaSecondFactor: {
        sms: false,
        otp: true,
      },
      userInvitation: {
        emailSubject: "Invite to join AWS DeepRacer Chatbot",
        emailBody:
          "Hello {username}, you have been invited to join AWS DeepRacer chatbot. \n" +
          "Your temporary password is \n\n{####}\n\n" +
          "https://" +
          props.distribution.distributionDomainName,
        smsMessage: "Hello {username}, your temporary password is {####}",
      },
      userVerification: {
        emailSubject: "Verify your email for AWS DeepRacer chatbot",
        emailBody:
          "Thanks for signing up to AWS DeepRacer chatbot \n\nYour verification code is \n{####}",
        emailStyle: cognito.VerificationEmailStyle.CODE,
        smsMessage:
          "Thanks for signing up to AWS DeepRacer chatbot. Your verification code is {####}",
      },
      lambdaTriggers: {
        postConfirmation: post_confirmation_lambda,
      },
      mfa: cognito.Mfa.OPTIONAL,
      advancedSecurityMode: cognito.AdvancedSecurityMode.ENFORCED,
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireDigits: true,
        requireSymbols: true,
        requireUppercase: true,
        tempPasswordValidity: cdk.Duration.days(2),
      },
    });

    post_confirmation_lambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["cognito-idp:AdminAddUserToGroup"],
        resources: ["*"], // TODO: wildcard used to get around circular dependency...
      })
    );

    const userPoolClient = userPool.addClient("UserPoolClient", {
      generateSecret: false,
      authFlows: {
        adminUserPassword: true,
        userPassword: true,
        userSrp: true,
      },
    });

    const identityPool = new cognitoIdentityPool.IdentityPool(
      this,
      "IdentityPool",
      {
        authenticationProviders: {
          userPools: [
            new cognitoIdentityPool.UserPoolAuthenticationProvider({
              userPool,
              userPoolClient,
            }),
          ],
        },
      }
    );

    // User Group Role
    const userGroupRole = new iam.Role(this, "UserGroupRole", {
      assumedBy: new iam.FederatedPrincipal(
        "cognito-identity.amazonaws.com",
        {
          StringEquals: {
            "cognito-identity.amazonaws.com:aud": identityPool.identityPoolId,
          },
          "ForAnyValue:StringLike": {
            "cognito-identity.amazonaws.com:amr": "authenticated",
          },
        },
        "sts:AssumeRoleWithWebIdentity"
      ),
    });
    this.authenticatedUserRole = identityPool.authenticatedRole;

    //  Cognito User Group (Racers)
    new cognito.CfnUserPoolGroup(this, "UsersGroup", {
      userPoolId: userPool.userPoolId,
      description: "normal users group",
      groupName: "Users",
      precedence: 1,
      roleArn: userGroupRole.roleArn,
    });

    this.userPool = userPool;
    this.userPoolClient = userPoolClient;
    this.identityPool = identityPool;

    new cdk.CfnOutput(this, "UserPoolId", {
      value: userPool.userPoolId,
    });

    new cdk.CfnOutput(this, "UserPoolWebClientId", {
      value: userPoolClient.userPoolClientId,
    });

    new cdk.CfnOutput(this, "UserPoolLink", {
      value: `https://${
        cdk.Stack.of(this).region
      }.console.aws.amazon.com/cognito/v2/idp/user-pools/${
        userPool.userPoolId
      }/users?region=${cdk.Stack.of(this).region}`,
    });

    new cdk.CfnOutput(this, "identityPoolId", {
      value: identityPool.identityPoolId,
    });
  }
}
