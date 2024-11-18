/* tslint:disable */
/* eslint-disable */
// this is an auto generated file. This will be overwritten

import * as APITypes from "../API";
type GeneratedQuery<InputType, OutputType> = string & {
  __generatedQueryInput: InputType;
  __generatedQueryOutput: OutputType;
};

export const getMessages = /* GraphQL */ `query GetMessages($maxResults: Int!) {
  getMessages(maxResults: $maxResults) {
    role
    content {
      text
      __typename
    }
    __typename
  }
}
` as GeneratedQuery<
  APITypes.GetMessagesQueryVariables,
  APITypes.GetMessagesQuery
>;
export const getModels = /* GraphQL */ `query GetModels {
  getModels {
    modelName
    status
    statusDetails
    __typename
  }
}
` as GeneratedQuery<APITypes.GetModelsQueryVariables, APITypes.GetModelsQuery>;
