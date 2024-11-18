from typing import Optional

import appsync_helpers
from aws_lambda_powertools import Logger

logger = Logger()


MUTATION_QUERY = """
mutation StreamResponse(
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
    content {
      text
      __typename
    }
    __typename
  }
}
"""


class StreamCallbackHandler:
    def __init__(
        self,
        user_id: str,
        session_id: str,
        message_id: str,
        chatbot_variant: str,
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.message_id = message_id
        self.chatbot_variant = chatbot_variant

    def __call__(self, message: str) -> None:
        """
        Send a StreamMessagePart mutation to trigger the onStreamMessagePart subscription.

        Args:
            message (dict): The message to be sent to Appsync.
        """

        variables = {
            "content": {"text": message},
            "chatbotVariant": self.chatbot_variant,
            "sessionId": self.session_id,
            "messageId": self.message_id,
            "userId": self.user_id,
        }

        logger.info(f"Sending mutation, variables: {variables}")

        try:
            response = appsync_helpers.send_mutation(MUTATION_QUERY, variables)
        except Exception as e:
            logger.exception(f"Error sending mutation: {e}")
            return None

        if "errors" in response:
            for error in response["errors"]:
                logger.error(f"GraphQL error: {error['message']}")
            return None

        logger.debug(f"Mutation response: {response}")
        return response
