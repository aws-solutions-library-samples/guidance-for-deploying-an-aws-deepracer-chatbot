import { useCallback, useState } from "react";

export interface FileProcessingHook {
  files: File[];
  setFiles: (files: File[]) => void;
  readFileAsBase64: (file: File) => Promise<string>;
  clearFiles: () => void;
}

export function useFileProcessing(): FileProcessingHook {
  const [files, setFiles] = useState<File[]>([]);
  
  const readFileAsBase64 = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64String = (reader.result as string).split(",")[1];
        resolve(base64String);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }, []);

  const clearFiles = useCallback(() => {
    setFiles([]);
  }, []);

  return {
    files,
    setFiles,
    readFileAsBase64,
    clearFiles,
  };
}