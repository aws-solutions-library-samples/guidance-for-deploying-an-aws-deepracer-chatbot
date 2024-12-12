import { FlashbarProps } from "@cloudscape-design/components";
import { UploadNotificationConfig } from "../types/upload";

export const createErrorNotification = ({
  message,
  dismissNotification,
}: {
  message: string;
  dismissNotification: (id: string) => void;
}): FlashbarProps.MessageDefinition => ({
  type: "error",
  dismissible: true,
  content: message,
  id: "errorNotification",
  onDismiss: () => dismissNotification("errorNotification"),
});

export const createUploadNotification = ({
  message,
  percentageUploaded,
  dismissNotification,
  type = "info",
}: UploadNotificationConfig): FlashbarProps.MessageDefinition => ({
  type: type as FlashbarProps.Type,
  dismissible: true,
  content: `${message} (${percentageUploaded}%)`,
  id: "uploadNotification",
  onDismiss: () => dismissNotification("uploadNotification"),
});
