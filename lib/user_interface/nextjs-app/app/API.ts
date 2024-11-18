/* tslint:disable */
/* eslint-disable */
//  This file was automatically generated and should not be edited.

export enum ChatbotVariant {
  questionsAndAnswers = "questionsAndAnswers",
  modelEvaluation = "modelEvaluation",
  rewardFunctionGeneration = "rewardFunctionGeneration",
}


export type ContentBlockInput = {
  text?: string | null,
  image?: ImageContentInput | null,
  document?: DocumentContentInput | null,
};

export type ImageContentInput = {
  format: ImageFormat,
  source: ImageSourceInput,
};

export enum ImageFormat {
  png = "png",
  jpeg = "jpeg",
  gif = "gif",
  webp = "webp",
}


export type ImageSourceInput = {
  bytes: string,
};

export type DocumentContentInput = {
  format: DocumentFormat,
  name: string,
  source: DocumentSourceInput,
};

export enum DocumentFormat {
  pdf = "pdf",
  csv = "csv",
  doc = "doc",
  docx = "docx",
  xls = "xls",
  xlsx = "xlsx",
  html = "html",
  txt = "txt",
  md = "md",
}


export type DocumentSourceInput = {
  bytes: string,
};

export type MessageReceipt = {
  __typename: "MessageReceipt",
  sessionId: string,
  messageId: string,
  status: MessageStatus,
  errorMessage?: string | null,
};

export enum MessageStatus {
  success = "success",
  error = "error",
}


export type ResponseContentBlockInput = {
  text?: string | null,
};

export type MessageResponse = {
  __typename: "MessageResponse",
  chatbotVariant?: ChatbotVariant | null,
  sessionId?: string | null,
  messageId?: string | null,
  userId?: string | null,
  role?: MessageRole | null,
  content?: ContentBlock | null,
};

export enum MessageRole {
  user = "user",
  assistant = "assistant",
}


export type ContentBlock = {
  __typename: "ContentBlock",
  text?: string | null,
};

export type ModelSubscription = {
  __typename: "ModelSubscription",
  models?:  Array<Model | null > | null,
  userId?: string | null,
};

export type Model = {
  __typename: "Model",
  modelName: string,
  status: ModelStatus,
  statusDetails?: string | null,
};

export enum ModelStatus {
  uploaded = "uploaded",
  ready = "ready",
  deleted = "deleted",
  error = "error",
}


export type Message = {
  __typename: "Message",
  role: MessageRole,
  content:  Array<ContentBlock >,
};

export type SendMessageMutationVariables = {
  chatbotVariant: ChatbotVariant,
  sessionId?: string | null,
  content: Array< ContentBlockInput >,
};

export type SendMessageMutation = {
  sendMessage:  {
    __typename: "MessageReceipt",
    sessionId: string,
    messageId: string,
    status: MessageStatus,
    errorMessage?: string | null,
  },
};

export type StreamResponseMutationVariables = {
  chatbotVariant: ChatbotVariant,
  sessionId: string,
  messageId: string,
  userId: string,
  content: ResponseContentBlockInput,
};

export type StreamResponseMutation = {
  streamResponse:  {
    __typename: "MessageResponse",
    chatbotVariant?: ChatbotVariant | null,
    sessionId?: string | null,
    messageId?: string | null,
    userId?: string | null,
    role?: MessageRole | null,
    content?:  {
      __typename: "ContentBlock",
      text?: string | null,
    } | null,
  },
};

export type DeleteModelsMutationVariables = {
  modelNames: Array< string | null >,
};

export type DeleteModelsMutation = {
  deleteModels:  {
    __typename: "ModelSubscription",
    models?:  Array< {
      __typename: "Model",
      modelName: string,
      status: ModelStatus,
      statusDetails?: string | null,
    } | null > | null,
    userId?: string | null,
  },
};

export type ModelAddedMutationVariables = {
  userId: string,
  modelName: string,
  status: ModelStatus,
  statusDetails?: string | null,
};

export type ModelAddedMutation = {
  modelAdded?:  {
    __typename: "ModelSubscription",
    models?:  Array< {
      __typename: "Model",
      modelName: string,
      status: ModelStatus,
      statusDetails?: string | null,
    } | null > | null,
    userId?: string | null,
  } | null,
};

export type GetMessagesQueryVariables = {
  maxResults: number,
};

export type GetMessagesQuery = {
  getMessages?:  Array< {
    __typename: "Message",
    role: MessageRole,
    content:  Array< {
      __typename: "ContentBlock",
      text?: string | null,
    } >,
  } > | null,
};

export type GetModelsQueryVariables = {
};

export type GetModelsQuery = {
  getModels?:  Array< {
    __typename: "Model",
    modelName: string,
    status: ModelStatus,
    statusDetails?: string | null,
  } | null > | null,
};

export type OnStreamResponseSubscriptionVariables = {
  userId: string,
};

export type OnStreamResponseSubscription = {
  onStreamResponse:  {
    __typename: "MessageResponse",
    chatbotVariant?: ChatbotVariant | null,
    sessionId?: string | null,
    messageId?: string | null,
    userId?: string | null,
    role?: MessageRole | null,
    content?:  {
      __typename: "ContentBlock",
      text?: string | null,
    } | null,
  },
};

export type OnModelAddedSubscriptionVariables = {
  userId?: string | null,
};

export type OnModelAddedSubscription = {
  onModelAdded?:  {
    __typename: "ModelSubscription",
    models?:  Array< {
      __typename: "Model",
      modelName: string,
      status: ModelStatus,
      statusDetails?: string | null,
    } | null > | null,
    userId?: string | null,
  } | null,
};

export type OnModelsDeletedSubscriptionVariables = {
  userId?: string | null,
};

export type OnModelsDeletedSubscription = {
  onModelsDeleted?:  {
    __typename: "ModelSubscription",
    models?:  Array< {
      __typename: "Model",
      modelName: string,
      status: ModelStatus,
      statusDetails?: string | null,
    } | null > | null,
    userId?: string | null,
  } | null,
};
