/**
 * @fileoverview Custom hook for handling file uploads with AWS Amplify Storage
 */

import { TransferProgressEvent } from "@aws-amplify/storage";
import { useAuthenticator } from "@aws-amplify/ui-react";
import { uploadData } from "aws-amplify/storage";
import { useState, useCallback, useEffect } from "react";
import { useLayoutContext } from "../contexts/layoutcontext";
import { UploadState } from "../types/upload";
import { createUploadNotification } from "../utils/notifications";
import { useFileProcessing } from "./useFileProcessing";

/**
 * Configuration constants for upload behavior
 * @constant
 */
const UPLOAD_CONFIG = {
  /** Access level for uploaded files */
  accessLevel: "private" as const,
  /** Threshold percentage for considering upload complete */
  progressThreshold: 100,
} as const;

/**
 * Calculates the upload progress percentage
 * @param {number} transferredBytes - Number of bytes transferred
 * @param {number | undefined} totalBytes - Total number of bytes to transfer
 * @returns {number} Percentage of upload completed (0-100)
 */
const calculateUploadProgress = (
  transferredBytes: number,
  totalBytes: number | undefined
): number => {
  if (!totalBytes) return 0;
  return Math.round((transferredBytes / totalBytes) * 100);
};

/**
 * Custom hook for managing file uploads with progress tracking and notifications
 *
 * @param {Function} onUploadSuccessful - Callback function called when upload completes successfully
 * @returns {Object} Object containing upload state and upload handler
 *
 * @example
 * const { uploadState, handleUpload } = useFileUpload((fileName) => {
 *   console.log(`${fileName} uploaded successfully`);
 * });
 */
export const useFileUpload = (
  onUploadSuccessful: (fileName: string) => void
) => {
  const { setFiles, clearFiles } = useFileProcessing();
  /**
   * State to track upload progress and file information
   */
  const [uploadState, setUploadState] = useState<UploadState>({
    percentageUploaded: 0,
    fileName: "",
  });

  const { addNotification, dismissNotification } = useLayoutContext();
  const { user } = useAuthenticator((context) => [context.authStatus]);

  /**
   * Handles upload progress events and updates state
   * @param {File} file - The file being uploaded
   * @param {TransferProgressEvent} progress - Progress event from AWS Amplify
   */
  const handleUploadProgress = (
    file: File,
    progress: TransferProgressEvent
  ) => {
    const percentage = calculateUploadProgress(
      progress.transferredBytes,
      progress.totalBytes
    );

    setUploadState((prev) => ({
      ...prev,
      percentageUploaded: percentage,
    }));

    if (percentage === UPLOAD_CONFIG.progressThreshold) {
      addNotification(
        createUploadNotification({
          message: `Uploaded: ${file.name}`,
          percentageUploaded: UPLOAD_CONFIG.progressThreshold,
          dismissNotification,
          type: "success",
        })
      );
      onUploadSuccessful(file.name);
    }
  };

  /**
   * Initiates the file upload process
   * @param {File} file - The file to upload
   * @throws Will throw an error if upload fails
   * @async
   */
  const handleUpload = async (file: File) => {
    try {
      setFiles([file]); // Track file in base hook
      // Reset upload state for new upload
      setUploadState({ fileName: file.name, percentageUploaded: 0 });

      // Create unique key for file using userId
      const key = `${user.userId}/${file.name}`;

      await uploadData({
        key,
        data: file,
        options: {
          accessLevel: UPLOAD_CONFIG.accessLevel,
          onProgress: (progress) => handleUploadProgress(file, progress),
        },
      }).result;
    } catch (error) {
      clearFiles(); // Clean up files on error
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
