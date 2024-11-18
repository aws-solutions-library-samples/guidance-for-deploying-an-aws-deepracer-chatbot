import LoadingBar from "@cloudscape-design/chat-components/loading-bar";
import { Container, Grid, SpaceBetween } from "@cloudscape-design/components";
import React, { useMemo } from "react";
import { MessageResponse, MessageRole } from "../../API";

interface TextWithLineBreaksProps {
  children?: string;
}

const TextWithLineBreaks: React.FC<TextWithLineBreaksProps> = React.memo(
  ({ children }) => {
    // Memoize the split operation
    const lines = useMemo(() => children?.split("\n") ?? [], [children]);

    return (
      <div>
        {lines.map((text, index) => (
          <React.Fragment key={index}>
            {text}
            {index < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>
    );
  }
);

const ChatMessage: React.FC<{ item: MessageResponse }> = React.memo(
  ({ item }) => {
    const isAssistant = useMemo(
      () => (item.role ?? MessageRole.assistant) === MessageRole.assistant,
      [item.role]
    );

    const messageDetails = useMemo(
      () => ({
        chatIcon: isAssistant ? "/chat-ai.png" : "/chat-human.png",
        altText: isAssistant ? MessageRole.assistant : MessageRole.user,
      }),
      [isAssistant]
    );

    return (
      <Container>
        <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
          <img src={messageDetails.chatIcon} alt={messageDetails.altText} />
          <code>
            <TextWithLineBreaks>{item.content?.text ?? ""}</TextWithLineBreaks>
          </code>
        </Grid>
      </Container>
    );
  }
);

interface ChatMessagesAreaProps {
  messages: MessageResponse[];
  waitingOnReply: boolean;
}

const ChatMessagesArea: React.FC<ChatMessagesAreaProps> = ({
  messages,
  waitingOnReply,
}) => {
  const mappedMessages = useMemo(
    () =>
      messages.map((item, index) => <ChatMessage key={index} item={item} />),
    [messages]
  );

  return (
    <SpaceBetween size="l" direction="vertical">
      {mappedMessages}
      {waitingOnReply && (
        <Container>
          <Grid gridDefinition={[{ colspan: 1 }, { colspan: 11 }]}>
            <img src="/chat-ai.png" alt="AI thinking" />
            <LoadingBar variant="gen-ai" />
          </Grid>
        </Container>
      )}
    </SpaceBetween>
  );
};

export default React.memo(ChatMessagesArea);
