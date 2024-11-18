/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedSubscription<InputType, OutputType> = string & {
  __generatedSubscriptionInput: InputType;
  __generatedSubscriptionOutput: OutputType;
};

export const onStreamResponse = /* GraphQL */ `subscription OnStreamResponse($userId: String!) {
  onStreamResponse(userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnStreamResponseSubscriptionVariables,
  APITypes.OnStreamResponseSubscription
>;
export const onModelAdded = /* GraphQL */ `subscription OnModelAdded($userId: String) {
  onModelAdded(userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnModelAddedSubscriptionVariables,
  APITypes.OnModelAddedSubscription
>;
export const onModelsDeleted = /* GraphQL */ `subscription OnModelsDeleted($userId: String) {
  onModelsDeleted(userId: $userId) {
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
` as GeneratedSubscription<
  APITypes.OnModelsDeletedSubscriptionVariables,
  APITypes.OnModelsDeletedSubscription
>;
