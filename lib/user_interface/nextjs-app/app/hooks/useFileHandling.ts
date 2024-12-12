import { useCallback } from "react";
import { ImageFormat } from "../API";
import { useFileProcessing } from "./useFileProcessing";

export function useFileHandling() {
  const { files, setFiles, readFileAsBase64 } = useFileProcessing();

  const processFiles = useCallback(async () => {
    const fileContents = await Promise.all(
      files.map(async (file) => {
        const base64Content = await readFileAsBase64(file);
        const format = file.type.split("/")[1] as ImageFormat;

        return {
          image: {
            format,
            source: { bytes: base64Content },
          },
        };
      })
    );

    return fileContents;
  }, [files]);

  return {
    files,
    setFiles,
    processFiles,
  };
}
