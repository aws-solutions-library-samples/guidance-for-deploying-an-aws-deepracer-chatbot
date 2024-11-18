#!/usr/bin/node

import { readFile, writeFile } from "fs/promises";

var awsExport = {
  aws_project_region: "eu-west-1",
  aws_appsync_graphqlEndpoint: "undefined",
  aws_appsync_region: "eu-west-1",
  aws_appsync_authenticationType: "AMAZON_COGNITO_USER_POOLS",
  aws_cognito_identity_pool_id: "undefined",
  aws_cognito_region: "eu-west-1",
  aws_user_pools_id: "undefined",
  aws_user_pools_web_client_id: "undefined",
  aws_user_files_s3_bucket_region: "eu-west-1",
  aws_user_files_s3_bucket: "undefined",
};

let outputs = JSON.parse(await readFile("./outputs.json", "utf8"));

for (const [key, value] of Object.entries(outputs)) {
  if (key.includes("-backend-")) {
    console.log("Backend");
    for (const [innerKey, innerValue] of Object.entries(value)) {
      if (innerKey.startsWith("apiawsappsyncgraphqlEndpoint")) {
        console.log("apiawsappsyncgraphqlEndpoint: ", innerValue);
        awsExport.aws_appsync_graphqlEndpoint = innerValue;
      } else if (innerKey.startsWith("ModelStorageModelBucketName")) {
        console.log("aws_user_files_s3_bucket: ", innerValue);
        awsExport.aws_user_files_s3_bucket = innerValue;
      }
    }
  } else if (key.includes("-")) {
    console.log("Main");
    for (const [innerKey, innerValue] of Object.entries(value)) {
      if (innerKey.startsWith("region")) {
        console.log("region: ", innerValue);
        awsExport.aws_appsync_region = innerValue;
        awsExport.aws_cognito_region = innerValue;
        awsExport.aws_project_region = innerValue;
        awsExport.aws_user_files_s3_bucket_region = innerValue;
      } else if (innerKey.startsWith("AuthenticationidentityPoolId")) {
        console.log("aws_cognito_identity_pool_id: ", innerValue);
        awsExport.aws_cognito_identity_pool_id = innerValue;
      } else if (
        innerKey.startsWith("ExportsOutputRefAuthenticationUserPool")
      ) {
        console.log("aws_user_pools_id: ", innerValue);
        awsExport.aws_user_pools_id = innerValue;
      } else if (innerKey.startsWith("AuthenticationUserPoolWebClientId")) {
        console.log("aws_user_pools_web_client_id: ", innerValue);
        awsExport.aws_user_pools_web_client_id = innerValue;
      }
    }
  }
}

// console.log(awsExport);
console.log("");
const awsExportString =
  "const awsExport = " +
  JSON.stringify(awsExport, null, 4) +
  "; \n\nexport default awsExport;";
console.log(awsExportString);
await writeFile(
  "lib/user_interface/nextjs-app/app/aws-exports.js",
  awsExportString
);
