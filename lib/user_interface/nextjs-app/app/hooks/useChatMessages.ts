import { useCallback, useState } from "react";
import { MessageResponse } from "../API";

export interface MessageWithFiles extends MessageResponse {
  files?: Array<{
    file: File;
  }>;
}

export function useChatMessages() {
  const [messages, setMessages] = useState<MessageWithFiles[]>([]);
  const [isWaitingReply, setWaitingReply] = useState(false);

  const addMessage = useCallback((message: MessageWithFiles) => {
    setMessages((prev) => {
      // If message has no messageId, just append it
      if (!message.messageId) {
        return [...prev, message];
      }

      // Find existing message with the same messageId
      const existingMessageIndex = prev.findIndex(
        (m) => m.messageId === message.messageId
      );

      if (existingMessageIndex === -1) {
        // No existing message with this messageId, append to the end
        return [...prev, message];
      }

      // Combine the content of the messages
      const existingMessage = prev[existingMessageIndex];
      const combinedMessage: MessageWithFiles = {
        ...existingMessage,
        content: {
          __typename: "ContentBlock",
          text: `${existingMessage.content?.text || ""}${message.content?.text || ""}`,
        },
        files: message.files,
      };

      // Create new array with the combined message replacing the existing one
      const newMessages = [...prev];
      newMessages[existingMessageIndex] = combinedMessage;
      return newMessages;
    });
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    addMessage,
    clearMessages,
    isWaitingReply,
    setWaitingReply,
  };
}
