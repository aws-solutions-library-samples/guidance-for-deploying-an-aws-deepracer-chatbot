import { FlashbarProps } from "@cloudscape-design/components";

export interface UploadNotificationConfig {
  message: string;
  percentageUploaded: number;
  dismissNotification: (id: string) => void;
  type?: FlashbarProps.Type;
}

export type UploadState = {
  percentageUploaded: number;
  fileName: string;
};
