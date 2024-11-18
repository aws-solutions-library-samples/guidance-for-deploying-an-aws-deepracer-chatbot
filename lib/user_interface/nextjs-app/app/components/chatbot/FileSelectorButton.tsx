import FileUpload, {
  FileUploadProps,
} from "@cloudscape-design/components/file-upload";
import React, { useCallback, useMemo } from "react";

interface FileSelectorButtonProps {
  onFileChange: (files: File[]) => void;
  maxFiles?: number;
  acceptedFileTypes?: string;
}

const FileSelectorButton: React.FC<FileSelectorButtonProps> = ({
  onFileChange,
  maxFiles = 3,
  acceptedFileTypes = ".png, .jpeg, .gif",
}) => {
  const handleChange = useCallback<NonNullable<FileUploadProps["onChange"]>>(
    ({ detail }) => onFileChange(detail.value),
    [onFileChange]
  );

  const i18nStrings = useMemo<FileUploadProps["i18nStrings"]>(
    () => ({
      uploadButtonText: (e) => (e ? "" : ""),
      dropzoneText: (e) =>
        e ? "" : "",
      removeFileAriaLabel: (e) => `Remove file ${e + 1}`,
      limitShowFewer: "Show fewer files",
      limitShowMore: "Show more files",
      errorIconAriaLabel: "Error",
    }),
    []
  );

  return (
    <FileUpload
      onChange={handleChange}
      accept={acceptedFileTypes}
      value={[]}
      i18nStrings={i18nStrings}
      multiple
      showFileLastModified
      showFileSize
      showFileThumbnail
      tokenLimit={maxFiles}
      className="chatbar_imageinput"
    />
  );
};

export default React.memo(FileSelectorButton);
