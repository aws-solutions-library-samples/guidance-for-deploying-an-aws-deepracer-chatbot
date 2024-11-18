/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedMutation<InputType, OutputType> = string & {
  __generatedMutationInput: InputType;
  __generatedMutationOutput: OutputType;
};

export const sendMessage = /* GraphQL */ `mutation SendMessage(
  $chatbotVariant: ChatbotVariant!
  $sessionId: ID
  $content: [ContentBlockInput!]!
) {
  sendMessage(
    chatbotVariant: $chatbotVariant
    sessionId: $sessionId
    content: $content
  ) {
    sessionId
    messageId
    status
    errorMessage
    __typename
  }
}
` as GeneratedMutation<
  APITypes.SendMessageMutationVariables,
  APITypes.SendMessageMutation
>;
export const streamResponse = /* GraphQL */ `mutation StreamResponse(
  $chatbotVariant: ChatbotVariant!
  $sessionId: ID!
  $messageId: ID!
  $userId: ID!
  $content: ResponseContentBlockInput!
) {
  streamResponse(
    chatbotVariant: $chatbotVariant
    sessionId: $sessionId
    messageId: $messageId
    userId: $userId
    content: $content
  ) {
    chatbotVariant
    sessionId
    messageId
    userId
    role
    content {
      text
      __typename
    }
    __typename
  }
}
` as GeneratedMutation<
  APITypes.StreamResponseMutationVariables,
  APITypes.StreamResponseMutation
>;
export const deleteModels = /* GraphQL */ `mutation DeleteModels($modelNames: [String]!) {
  deleteModels(modelNames: $modelNames) {
    models {
      modelName
      status
      statusDetails
      __typename
    }
    userId
    __typename
  }
}
` as GeneratedMutation<
  APITypes.DeleteModelsMutationVariables,
  APITypes.DeleteModelsMutation
>;
export const modelAdded = /* GraphQL */ `mutation ModelAdded(
  $userId: ID!
  $modelName: String!
  $status: ModelStatus!
  $statusDetails: String
) {
  modelAdded(
    userId: $userId
    modelName: $modelName
    status: $status
    statusDetails: $statusDetails
  ) {
    models {
      modelName
      status
      statusDetails
      __typename
    }
    userId
    __typename
  }
}
` as GeneratedMutation<
  APITypes.ModelAddedMutationVariables,
  APITypes.ModelAddedMutation
>;
