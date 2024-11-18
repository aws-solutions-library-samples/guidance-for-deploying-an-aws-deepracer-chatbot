import { useCallback, useState } from "react";
import { ImageContentInput, ImageFormat, ImageSourceInput } from "../API";
import { convertToBase64AndRaw, resizeImage } from "../utils/imageUtils";

/**
 * Custom hook for processing images
 * @param width - The desired width of the processed image
 * @param height - The desired height of the processed image
 * @returns Object containing processImages function, clearImages function, thumbnails, and imageInputs
 */
export default function useImageProcessing(width: number, height: number) {
  const [thumbnails, setThumbnails] = useState<string[]>([]);
  const [imageInputs, setImageInputs] = useState<ImageContentInput[]>([]);

  const processImages = useCallback(
    async (
      files: File[]
    ): Promise<{ thumbnails: string[]; imageInputs: ImageContentInput[] }> => {
      // Input validation
      if (width <= 0 || height <= 0) {
        throw new Error("Width and height must be positive numbers");
      }

      try {
        const processedImages = await Promise.all(
          files.map(async (file) => {
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
