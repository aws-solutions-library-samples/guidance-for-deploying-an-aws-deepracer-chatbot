import {
  Button,
  Container,
  ExpandableSection,
} from "@cloudscape-design/components";
import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { ChatbotVariant, MessageResponse } from "../../API";
import ChatDefaultsArea from "./ChatDefaultsArea";
import ChatMessagesArea from "./ChatMessageArea";
import ChatSendMessage from "./ChatSendMessage";
import styles from "./ChatWindow.module.css";

const MemoizedChatMessagesArea = memo(ChatMessagesArea);

interface ChatWindowProps {
  chatbotType: ChatbotVariant;
  sessionId: string;
  defaultPrompts: string[];
}

export default function ChatWindow({
  chatbotType,
  sessionId,
  defaultPrompts,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [messageMap, setMessageMap] = useState(
    new Map<string, MessageResponse>()
  );
  const [waitingOnReply, setWaitingOnReply] = useState<boolean>(false);
  const [showDefaultPrompts, setShowDefaultPrompts] = useState<boolean>(true);

  const accumulateMessage = useCallback(
    (
      prevMessages: MessageResponse[],
      message: MessageResponse
    ): MessageResponse[] => {
      const addKey = (msg: MessageResponse) => ({
        ...msg,
        key: msg.messageId || Date.now().toString(),
      });

      // If no messageId, just append the message
      if (!message.messageId) {
        return [...prevMessages, addKey(message)];
      }

      // Check if message exists in the map
      if (!messageMap.has(message.messageId)) {
        setMessageMap(new Map(messageMap.set(message.messageId, message)));
        return [...prevMessages, message];
      }

      const updatedMessages = [...prevMessages];
      const existingMessageIndex = prevMessages.findIndex(
        (m) => m.messageId === message.messageId
      );

      // If message not found in the array, return with new message
      if (existingMessageIndex === -1) {
        return [...prevMessages, message];
      }

      const existingMessage = updatedMessages[existingMessageIndex];

      // Safely handle content updates
      if (existingMessage && existingMessage.content && message.content) {
        existingMessage.content.text =
          (existingMessage.content?.text || "") + (message.content?.text || "");
      } else if (message.content && existingMessage) {
        existingMessage.content = message.content;
      }

      return updatedMessages.map(addKey);
    },
    [messageMap]
  );

  const onNewMessageHandler = useCallback(
    (message: MessageResponse, thumbnails: string[]) => {
      setShowDefaultPrompts(false);
      setMessages((prevMessages) => accumulateMessage(prevMessages, message));
    },
    [accumulateMessage]
  );

  const onWaitingReplyHandler = useCallback((waiting: boolean) => {
    setWaitingOnReply(waiting);
  }, []);

  const onClearMessagesHandler = useCallback(() => {
    setMessages([]);
    setMessageMap(new Map());
    setShowDefaultPrompts(true);
  }, []);

  const footer = useMemo(
    () => (
      <ChatSendMessage
        sessionId={sessionId}
        onNewMessage={onNewMessageHandler}
        onWaitingReply={onWaitingReplyHandler}
        onClearMessages={onClearMessagesHandler}
        chatbotVariant={chatbotType}
      />
    ),
    [
      sessionId,
      onNewMessageHandler,
      onWaitingReplyHandler,
      onClearMessagesHandler,
      chatbotType,
    ]
  );

  // Cleanup effect
  useEffect(() => {
    return () => {
      setMessageMap(new Map());
      setMessages([]);
    };
  }, []);

  return (
    <div className={styles.workArea}>
      <Container fitHeight={true} footer={footer} className="chatWindow">
        <ChatDefaultsArea
          display={showDefaultPrompts}
          prompts={defaultPrompts}
        />
        <MemoizedChatMessagesArea
          messages={messages}
          waitingOnReply={waitingOnReply}
        />
      </Container>
      <ExpandableSection variant="footer" headerText="Settings">
        <Button
          iconName="status-warning"
          loading={waitingOnReply}
          onClick={onClearMessagesHandler}
          variant="normal"
          fullWidth={false}
        >
          Clear chat
        </Button>
      </ExpandableSection>
    </div>
  );
}
