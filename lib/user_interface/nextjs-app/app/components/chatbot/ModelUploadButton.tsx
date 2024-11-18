import FileUpload from "@cloudscape-design/components/file-upload";
import { FC, useEffect } from "react";
import { useLayoutContext } from "../../contexts/layoutcontext";
import { useFileUpload } from "../../hooks/useFileUpload";
import { createUploadNotification } from "../../utils/notifications";

type Props = {
  onUploadSuccessful: (fileName: string) => void;
};

// Constants
const FILE_UPLOAD_STRINGS = {
  uploadButtonText: () => "Upload model",
  dropzoneText: () => "Drop model to upload",
  removeFileAriaLabel: (index: number) => `Remove file ${index + 1}`,
  limitShowFewer: "Show fewer files",
  limitShowMore: "Show more files",
  errorIconAriaLabel: "Error",
} as const;

const ModelUploadButton: FC<Props> = ({ onUploadSuccessful }) => {
  const { uploadState, handleUpload } = useFileUpload(onUploadSuccessful);
  const { addNotification, dismissNotification } = useLayoutContext();

  useEffect(() => {
    const { percentageUploaded, fileName } = uploadState;
    if (percentageUploaded > 0 && percentageUploaded < 100) {
      addNotification(
        createUploadNotification({
          message: `Uploading: ${fileName}`,
          percentageUploaded,
          dismissNotification,
        })
      );
    }
  }, [uploadState, dismissNotification, addNotification]);

  return (
    <FileUpload
      onChange={({ detail }) =>
        detail.value[0] && handleUpload(detail.value[0])
      }
      accept=".gz, .zip"
      value={[]}
      i18nStrings={FILE_UPLOAD_STRINGS}
      showFileLastModified
      showFileSize
      showFileThumbnail
      tokenLimit={3}
    />
  );
};

export default ModelUploadButton;
