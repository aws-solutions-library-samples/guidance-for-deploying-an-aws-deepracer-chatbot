import { useAuthenticator } from "@aws-amplify/ui-react";
import Box from "@cloudscape-design/components/box";
import FileInput from "@cloudscape-design/components/file-input";
import FileTokenGroup from "@cloudscape-design/components/file-token-group";
import PromptInput from "@cloudscape-design/components/prompt-input";
import { generateClient } from "aws-amplify/api";
import { ImageFormat, MessageReceipt, MessageRole } from "../../API";
import { sendMessage } from "../../graphql/mutations";

import React, { FC, useCallback, useEffect, useReducer } from "react";
import { ChatbotVariant, MessageResponse } from "../../API";
import useSubscription from "../../hooks/useSubscription";
import {
  ChatActionType,
  chatReducer,
  initialChatState,
} from "../../reducers/chatReducer";

interface Props {
  onNewMessage: (message: MessageResponse, thumbnails: string[]) => void;
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
  const [files, setFiles] = React.useState<File[]>([]);

  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const { messageToSend, sendButtonDisabled, noRowsMessageBox } = chatState;

  const { subscriptionConnected, setupSubscription, subscriptionHandler } =
    useSubscription(user.userId, sessionId, onNewMessage, onWaitingReply);

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

    // Function to read file as base64
    const readFileAsBase64 = (file: File): Promise<string> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          // Remove the "data:image/xxx;base64," prefix from the result
          const base64String = (reader.result as string).split(",")[1];
          resolve(base64String);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    };

    try {
      // Read all files concurrently
      const fileContents = await Promise.all(
        files.map(async (file) => {
          const base64Content = await readFileAsBase64(file);
          const format = file.type.split("/")[1] as ImageFormat;

          return {
            image: {
              format,
              source: { bytes: base64Content },
            },
          };
        })
      );

      const content = [{ text: messageToSend }, ...fileContents];

      onNewMessage(
        {
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
        },
        []
      );

      dispatch({ type: ChatActionType.RESET_MESSAGE_STATE });
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
        console.error(response.errorMessage);
      }
    } catch (error) {
      console.error(error);
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
        disableActionButton={sendButtonDisabled}
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
              onDismiss={({ detail }) =>
                setFiles((files) =>
                  files.filter((_, index) => index !== detail.fileIndex)
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
