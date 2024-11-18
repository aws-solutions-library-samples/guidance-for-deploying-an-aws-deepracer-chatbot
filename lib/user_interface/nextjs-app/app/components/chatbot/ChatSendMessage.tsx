import { useAuthenticator } from "@aws-amplify/ui-react";
import { Button, Textarea } from "@cloudscape-design/components";
import { generateClient } from "aws-amplify/api";
import React, {
  FC,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from "react";
import {
  ChatbotVariant,
  ImageContentInput,
  ImageFormat,
  MessageReceipt,
  MessageResponse,
  MessageRole,
} from "../../API";
import { sendMessage } from "../../graphql/mutations";
import useImageProcessing from "../../hooks/useImageProcessing";
import useSubscription from "../../hooks/useSubscription";
import { chatReducer, initialChatState } from "../../reducers/chatReducer";
import FileSelectorButton from "./FileSelectorButton";
import ThumbnailList from "./ThumbnailList";

// Constants
const IMAGE_RESIZE_WIDTH = 200;
const IMAGE_RESIZE_HEIGHT = 200;

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

  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const { messageToSend, sendButtonDisabled, noRowsMessageBox } = chatState;

  const { processImages, clearImages, thumbnails, imageInputs } =
    useImageProcessing(IMAGE_RESIZE_WIDTH, IMAGE_RESIZE_HEIGHT);

  const { subscriptionConnected, setupSubscription, subscriptionHandler } =
    useSubscription(user.userId, sessionId, onNewMessage, onWaitingReply);

  useEffect(() => {
    setupSubscription();

    return () => {
      console.log("Unsubscribe from subscription");
      subscriptionHandler?.unsubscribe();
    };
  }, []);

  const handleNewUploadedFile = useCallback(
    async (uploadedNewFiles: File[]) => {
      const result: { thumbnails: string[]; imageInputs: ImageContentInput[] } =
        await processImages(uploadedNewFiles);
      dispatch({ type: "SET_THUMBNAILS_AND_INPUTS", payload: result });
    },
    [processImages]
  );

  const handleSendMessage = useCallback(async () => {
    if (!messageToSend) return;

    dispatch({ type: "SET_SEND_BUTTON_DISABLED", payload: true });
    onWaitingReply(true);

    const content = [
      { text: messageToSend },
      ...imageInputs.map((img) => ({
        image: {
          format: img.format as ImageFormat,
          source: { bytes: img.source.bytes },
        },
      })),
    ];

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
      thumbnails
    );

    try {
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

      dispatch({ type: "RESET_MESSAGE_STATE" });
      clearImages();
    } catch (error) {
      console.error(error);
    } finally {
      dispatch({ type: "SET_SEND_BUTTON_DISABLED", payload: false });
    }
  }, [
    messageToSend,
    imageInputs,
    thumbnails,
    sessionId,
    subscriptionConnected,
    client,
    chatbotVariant,
    onNewMessage,
    onWaitingReply,
    user.userId,
  ]);

  // const handleClearMessages = useCallback(() => {
  //   onClearMessages();
  //   dispatch({ type: "RESET_ALL" });
  // }, [onClearMessages]);

  const inputRef = useRef<HTMLInputElement>(null);

  const fileSelectorButtonContent = useMemo(
    () =>
      !sendButtonDisabled ? (
        <FileSelectorButton onFileChange={handleNewUploadedFile} />
      ) : null,
    [sendButtonDisabled, handleNewUploadedFile]
  );

  useEffect(() => {
    if (!sendButtonDisabled) {
      inputRef.current?.focus();
    }
  }, [sendButtonDisabled]);

  const memoizedThumbnailList = useMemo(
    () =>
      thumbnails.length > 0 ? <ThumbnailList thumbnails={thumbnails} /> : "",
    [thumbnails]
  );

  return (
    <div className="footerblock">
      <Textarea
        onChange={({ detail }) =>
          dispatch({ type: "SET_MESSAGE_TO_SEND", payload: detail.value })
        }
        value={messageToSend}
        autoFocus={true}
        disabled={sendButtonDisabled}
        placeholder="Write a prompt... (Shift + ENTER for new line, ENTER to send)"
        rows={noRowsMessageBox}
        onKeyDown={(e) => {
          if (e.detail.key === "Enter" && !e.detail.shiftKey) {
            e.preventDefault();
            handleSendMessage();
          } else if (e.detail.key === "Enter" && e.detail.shiftKey) {
            dispatch({ type: "INCREMENT_ROWS" });
          }
        }}
        ref={inputRef}
        className="chatbar_textinput"
      />
      {fileSelectorButtonContent}
      <Button
        iconName="caret-right-filled"
        loading={sendButtonDisabled}
        onClick={handleSendMessage}
        variant="primary"
        fullWidth={true}
        className="chatbar_submit"
      />
      {memoizedThumbnailList}
    </div>
  );
};

export default React.memo(ChatSendMessage);
