// hooks/useFileUpload.ts
import { useAuthenticator } from "@aws-amplify/ui-react";
import { uploadData } from "aws-amplify/storage";
import { useState } from "react";
import { useLayoutContext } from "../contexts/layoutcontext";
import { UploadState } from "../types/upload";
import { createUploadNotification } from "../utils/notifications";

export const useFileUpload = (
  onUploadSuccessful: (fileName: string) => void
) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    percentageUploaded: 0,
    fileName: "",
  });

  const { addNotification, dismissNotification } = useLayoutContext();
  const { user } = useAuthenticator((context) => [context.authStatus]);

  const handleUpload = async (file: File) => {
    try {
      setUploadState({ fileName: file.name, percentageUploaded: 0 });
      const key = `${user.userId}/${file.name}`;

      await uploadData({
        key,
        data: file,
        options: {
          accessLevel: "private",
          onProgress: ({ transferredBytes, totalBytes }) => {
            if (!totalBytes) return;

            const percentage = Math.round(
              (transferredBytes / totalBytes) * 100
            );
            setUploadState((prev) => ({
              ...prev,
              percentageUploaded: percentage,
            }));

            if (percentage === 100) {
              addNotification(
                createUploadNotification({
                  message: `Uploaded: ${file.name}`,
                  percentageUploaded: 100,
                  dismissNotification,
                  type: "success",
                })
              );
              onUploadSuccessful(file.name);
            }
          },
        },
      }).result;
    } catch (error) {
      console.error("Upload error:", error);
      addNotification(
        createUploadNotification({
          message: `Upload failed: ${file.name}`,
          percentageUploaded: 0,
          dismissNotification,
          type: "error",
        })
      );
    }
  };

  return { uploadState, handleUpload };
};
