import { FlashbarProps } from "@cloudscape-design/components";
import { UploadNotificationConfig } from "../types/upload";

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
