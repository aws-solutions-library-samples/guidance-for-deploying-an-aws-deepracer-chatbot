import Avatar from "@cloudscape-design/chat-components/avatar";
import ChatBubble from "@cloudscape-design/chat-components/chat-bubble";
import { SpaceBetween } from "@cloudscape-design/components";
import Box from "@cloudscape-design/components/box";
import ButtonGroup from "@cloudscape-design/components/button-group";
import FileTokenGroup from "@cloudscape-design/components/file-token-group";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import React, { useMemo } from "react";
import { MessageRole } from "../../API";
import { MessageWithFiles } from "../../hooks/useChatMessages";
import MessageRenderer from "./MessageRenderer";

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

const ChatMessage: React.FC<{ item: MessageWithFiles }> = React.memo(
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
          <React.Suspense fallback={<div>Loading...</div>}>
            <MessageRenderer text={item.content?.text ?? ""} />
          </React.Suspense>
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
        <SpaceBetween size="s">
          <React.Suspense fallback={<div>Loading...</div>}>
            <MessageRenderer text={item.content?.text ?? ""} />
          </React.Suspense>
          {item.files && item.files.length > 0 && (
            <FileTokenGroup
              items={item.files}
              readOnly
              showFileSize
              showFileThumbnail
              onDismiss={() => {}}
              i18nStrings={{
                errorIconAriaLabel: "Error",
                warningIconAriaLabel: "Warning",
                removeFileAriaLabel: () => "Remove file",
              }}
            />
          )}
        </SpaceBetween>
      </ChatBubble>
    );
  }
);

interface ChatMessagesAreaProps {
  messages: MessageWithFiles[];
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
