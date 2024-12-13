import { useAuthenticator } from "@aws-amplify/ui-react";
import Box from "@cloudscape-design/components/box";
import FileInput from "@cloudscape-design/components/file-input";
import FileTokenGroup from "@cloudscape-design/components/file-token-group";
import PromptInput from "@cloudscape-design/components/prompt-input";
import { generateClient } from "aws-amplify/api";
import { MessageReceipt, MessageRole } from "../../API";
import { sendMessage } from "../../graphql/mutations";
import { MessageWithFiles } from "../../hooks/useChatMessages";
import { useFileHandling } from "../../hooks/useFileHandling";
import { createErrorNotification } from "../../utils/notifications";

import React, { FC, useCallback, useEffect, useReducer } from "react";
import { ChatbotVariant } from "../../API";
import { useLayoutContext } from "../../contexts/layoutcontext";
import useSubscription from "../../hooks/useSubscription";
import {
  ChatActionType,
  chatReducer,
  initialChatState,
} from "../../reducers/chatReducer";

interface Props {
  onNewMessage: (message: MessageWithFiles) => void;
  onWaitingReply: (waiting: boolean) => void;
  onClearMessages: () => void;
  chatbotVariant: ChatbotVariant;
  sessionId: string;
}

const ChatSendMessage: FC<Props> = ({
  onNewMessage,
  onWaitingReply,
  onClearMessages,
  chatbotVariant,
  sessionId,
}) => {
  const { authStatus, user } = useAuthenticator((context) => [
    context.authStatus,
  ]);
  const client = generateClient();
  const { files, setFiles, processFiles } = useFileHandling();

  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const { messageToSend, sendButtonDisabled, noRowsMessageBox } = chatState;
  const { addNotification, dismissNotification } = useLayoutContext();

  const { subscriptionConnected, setupSubscription, subscriptionHandler } =
    useSubscription(user.userId, onNewMessage, onWaitingReply);

  useEffect(() => {
    setupSubscription();

    return () => {
      console.log("Unsubscribe from subscription");
      subscriptionHandler?.unsubscribe();
    };
  }, []);

  const handleSendMessage = useCallback(async () => {
    if (!messageToSend) return;

    dispatch({ type: ChatActionType.SET_SEND_BUTTON_DISABLED, payload: true });
    onWaitingReply(true);

    try {
      const fileContents = await processFiles();

      const content = [{ text: messageToSend }, ...fileContents];

      onNewMessage({
        __typename: "MessageResponse",
        chatbotVariant,
        sessionId,
        messageId: crypto.randomUUID(),
        userId: user.userId,
        role: MessageRole.user,
        content: {
          __typename: "ContentBlock",
          text: messageToSend,
        },
        files: files.map((file) => ({
          file: file,
        })),
      });

      // clear the prompt input after message been sent
      dispatch({ type: ChatActionType.SET_MESSAGE_TO_SEND, payload: "" });
      setFiles([]);

      const response = (
        await client.graphql({
          query: sendMessage,
          variables: {
            chatbotVariant,
            sessionId,
            content,
          },
        })
      ).data.sendMessage as MessageReceipt;

      if (response.status === "success") {
        console.log("Message sent successfully");
      } else {
        console.error("Error sending message:", response.errorMessage);
        addNotification(
          createErrorNotification({
            message:
              response.errorMessage ||
              "An error occurred while sending the message",
            dismissNotification,
          })
        );
      }
    } catch (error) {
      console.error("Error sending message 1:", error);
      let errorMessage = "An error occurred while sending the message";

      // Handle GraphQL errors array structure
      if (error && Array.isArray((error as any).errors)) {
        const graphqlError = (error as any).errors[0];
        if (graphqlError && graphqlError.message) {
          errorMessage = graphqlError.message;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      addNotification(
        createErrorNotification({
          message: errorMessage,
          dismissNotification,
        })
      );

      onWaitingReply(false);
      onNewMessage({
        __typename: "MessageResponse",
        chatbotVariant,
        sessionId,
        messageId: crypto.randomUUID(),
        role: MessageRole.assistant,
        content: {
          __typename: "ContentBlock",
          text: "An error occurred while sending the message",
        },
      });
    } finally {
      dispatch({
        type: ChatActionType.SET_SEND_BUTTON_DISABLED,
        payload: false,
      });
    }
  }, [
    messageToSend,
    files,
    sessionId,
    subscriptionConnected,
    client,
    chatbotVariant,
    onNewMessage,
    onWaitingReply,
    user.userId,
  ]);

  return (
    <>
      <PromptInput
        onChange={({ detail }) =>
          dispatch({
            type: ChatActionType.SET_MESSAGE_TO_SEND,
            payload: detail.value,
          })
        }
        value={messageToSend}
        ariaLabel="Default prompt input"
        placeholder="Write a prompt... (Shift + ENTER for new line, ENTER to send)"
        autoFocus
        actionButtonAriaLabel="Send message"
        actionButtonIconName="send"
        spellcheck
        disabled={sendButtonDisabled}
        onAction={({ detail }) => {
          console.info(detail.value);
          handleSendMessage();
        }}
        secondaryActions={
          <Box padding={{ left: "xxs", top: "xs" }}>
            <FileInput
              variant="icon"
              accept=".png, .jpeg"
              multiple={true}
              value={files}
              onChange={({ detail }) => {
                console.info(detail.value);
                setFiles(detail.value);
              }}
            />
          </Box>
        }
        secondaryContent={
          files.length > 0 && (
            <FileTokenGroup
              items={files.map((file) => ({ file }))}
              onDismiss={({ detail }: { detail: { fileIndex: number } }) =>
                setFiles(
                  files.filter((_, index: number) => index !== detail.fileIndex)
                )
              }
              alignment="horizontal"
              showFileSize={true}
              showFileLastModified={true}
              showFileThumbnail={true}
              i18nStrings={{
                removeFileAriaLabel: () => "Remove file",
                limitShowFewer: "Show fewer files",
                limitShowMore: "Show more files",
                errorIconAriaLabel: "Error",
                warningIconAriaLabel: "Warning",
              }}
            />
          )
        }
      />
    </>
  );
};

export default React.memo(ChatSendMessage);
