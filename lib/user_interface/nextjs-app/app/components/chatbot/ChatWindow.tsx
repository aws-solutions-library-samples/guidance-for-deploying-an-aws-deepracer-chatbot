import { Container } from "@cloudscape-design/components";
import { ChatbotVariant } from "../../API";
import { useChatMessages } from "../../hooks/useChatMessages";
import ChatDefaultsArea from "./ChatDefaultsArea";
import ChatMessagesArea from "./ChatMessageArea";
import ChatSendMessage from "./ChatSendMessage";
import styles from "./ChatWindow.module.css";

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
  const {
    messages,
    addMessage,
    clearMessages,
    isWaitingReply,
    setWaitingReply,
  } = useChatMessages();

  const showDefaultPrompts = messages.length === 0;

  return (
    <div className={styles.workArea}>
      <Container
        fitHeight
        footer={
          <ChatSendMessage
            sessionId={sessionId}
            onNewMessage={addMessage}
            onWaitingReply={setWaitingReply}
            onClearMessages={clearMessages}
            chatbotVariant={chatbotType}
          />
        }
        className="chatWindow"
      >
        {showDefaultPrompts && (
          <ChatDefaultsArea
            prompts={defaultPrompts}
            display={showDefaultPrompts}
          />
        )}
        <ChatMessagesArea messages={messages} waitingOnReply={isWaitingReply} />
      </Container>
    </div>
  );
}
