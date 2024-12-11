import Avatar from "@cloudscape-design/chat-components/avatar";
import ChatBubble from "@cloudscape-design/chat-components/chat-bubble";
import { SpaceBetween } from "@cloudscape-design/components";
import Box from "@cloudscape-design/components/box";
import ButtonGroup from "@cloudscape-design/components/button-group";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import React, { useMemo } from "react";
import { MessageResponse, MessageRole } from "../../API";

const useFormattedTime = () => {
  return useMemo(() => {
    return new Date().toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
  }, []);
};

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

    const currentTime = useFormattedTime();
    if (isAssistant) {
      return (
        <ChatBubble
          ariaLabel={`Generative AI assistant at ${currentTime}`}
          type="incoming"
          actions={
            <ButtonGroup
              ariaLabel="Chat bubble actions"
              variant="icon"
              items={[
                {
                  type: "icon-button",
                  id: "copy",
                  iconName: "copy",
                  text: "Copy",
                  popoverFeedback: (
                    <StatusIndicator type="success">
                      Message copied
                    </StatusIndicator>
                  ),
                },
              ]}
            />
          }
          avatar={
            <Avatar
              color="gen-ai"
              iconName="gen-ai"
              ariaLabel="Generative AI assistant"
              tooltipText="Generative AI assistant"
            />
          }
        >
          {item.content?.text ?? ""}
        </ChatBubble>
      );
    }

    return (
      <ChatBubble
        ariaLabel={`User at ${currentTime}`}
        type="outgoing"
        avatar={<Avatar ariaLabel="User" tooltipText="User" initials="U" />}
        actions={
          <ButtonGroup
            ariaLabel="Chat bubble actions"
            variant="icon"
            items={[
              {
                type: "icon-button",
                id: "copy",
                iconName: "copy",
                text: "Copy",
                popoverFeedback: (
                  <StatusIndicator type="success">
                    Message copied
                  </StatusIndicator>
                ),
              },
            ]}
          />
        }
      >
        {item.content?.text ?? ""}
      </ChatBubble>
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

  const currentTime = useFormattedTime();

  return (
    <SpaceBetween size="l" direction="vertical">
      {mappedMessages}
      {waitingOnReply && (
        <ChatBubble
          ariaLabel={`Generative AI assistant at ${currentTime}`}
          type="incoming"
          avatar={
            <Avatar
              loading={true}
              color="gen-ai"
              iconName="gen-ai"
              ariaLabel="Generative AI assistant"
              tooltipText="Generative AI assistant"
            />
          }
        >
          <Box color="text-status-inactive">Generating response...</Box>
        </ChatBubble>
      )}
    </SpaceBetween>
  );
};

export default React.memo(ChatMessagesArea);
