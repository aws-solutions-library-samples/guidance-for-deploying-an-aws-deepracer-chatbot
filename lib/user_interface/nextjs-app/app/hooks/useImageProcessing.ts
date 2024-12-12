import { useCallback, useState } from "react";
import { ImageContentInput, ImageFormat, ImageSourceInput } from "../API";
import { convertToBase64AndRaw, resizeImage } from "../utils/imageUtils";
import { useFileProcessing } from "./useFileProcessing";

export interface ImageProcessingHook {
  files: File[];
  thumbnails: string[];
  imageInputs: ImageContentInput[];
  processImages: (selectedFiles: File[]) => Promise<void>;
  clearImages: () => void;
}

/**
 * Custom hook for processing images using the base file processing hook
 * @param width - The desired width of the processed image
 * @param height - The desired height of the processed image
 * @returns Object containing image processing functions and state
 */
export function useImageProcessing(width: number, height: number): ImageProcessingHook {
  const { files, setFiles, clearFiles } = useFileProcessing();
  const [thumbnails, setThumbnails] = useState<string[]>([]);
  const [imageInputs, setImageInputs] = useState<ImageContentInput[]>([]);

  const processImages = useCallback(
    async (selectedFiles: File[]) => {
      // Input validation
      if (width <= 0 || height <= 0) {
        throw new Error("Width and height must be positive numbers");
      }

      setFiles(selectedFiles);

      try {
        const processedImages = await Promise.all(
          selectedFiles.map(async (file) => {
            const resizedImage = await resizeImage(file, width, height);
            const { dataUrl: thumbnail, rawBase64: base64 } =
              await convertToBase64AndRaw(resizedImage);
            const imageSource: ImageSourceInput = {
              bytes: base64,
            };
            const imageInput: ImageContentInput = {
              format: resizedImage.type.split("/")[1] as ImageFormat,
              source: imageSource,
            };
            return { thumbnail, imageInput };
          })
        );

        const newThumbnails = processedImages.map(({ thumbnail }) => thumbnail);
        const newImageInputs = processedImages.map(
          ({ imageInput }) => imageInput
        );

        setThumbnails((prev) => [...prev, ...newThumbnails]);
        setImageInputs((prev) => [...prev, ...newImageInputs]);

        return { thumbnails: newThumbnails, imageInputs: newImageInputs };
      } catch (error) {
        console.error("Error processing images:", error);
        throw error;
      }
    },
    [width, height]
  );

  /**
   * Clears all stored images by resetting thumbnails and imageInputs to empty arrays.
   */
  const clearImages = useCallback(() => {
    setThumbnails([]);
    setImageInputs([]);
  }, []);

  return { processImages, clearImages, thumbnails, imageInputs };
}
