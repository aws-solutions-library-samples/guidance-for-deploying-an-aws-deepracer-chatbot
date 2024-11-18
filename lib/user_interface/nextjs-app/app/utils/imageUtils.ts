export const resizeImage = (
  image: File,
  maxWidth: number,
  maxHeight: number
): Promise<File> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      reject(new Error("Failed to create canvas context"));
      return;
    }

    const img = new Image();
    img.src = URL.createObjectURL(image);

    img.onload = () => {
      const originalWidth = img.width;
      const originalHeight = img.height;

      let newWidth = maxWidth;
      let newHeight = maxHeight;

      // Calculate the new dimensions while preserving the aspect ratio
      if (originalWidth > originalHeight) {
        newHeight = Math.floor((originalHeight * maxWidth) / originalWidth);
      } else {
        newWidth = Math.floor((originalWidth * maxHeight) / originalHeight);
      }

      canvas.width = newWidth;
      canvas.height = newHeight;
      ctx.drawImage(img, 0, 0, newWidth, newHeight);

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error("Failed to create resized image blob"));
            return;
          }

          const resizedFile = new File([blob], image.name, {
            type: image.type,
          });
          resolve(resizedFile);
        },
        image.type,
        1
      );

      URL.revokeObjectURL(img.src);
    };

    img.onerror = () => {
      reject(new Error("Failed to load image"));
    };
  });
};

/**
 * Converts a File to both a data URL and a raw Base64-encoded string.
 *
 * This function reads the file as an ArrayBuffer and then converts it to two formats:
 * 1. A data URL, which includes the MIME type and can be used directly in image src attributes.
 * 2. A raw Base64-encoded string of the file's binary content.
 *
 * @param {File} file - The File object to be converted.
 * @returns {Promise<{dataUrl: string, rawBase64: string}>} A Promise that resolves to an object containing:
 *   - dataUrl: A string representing the file as a data URL (e.g., "data:image/jpeg;base64,/9j/4AAQSkZJRg...")
 *   - rawBase64: A string representing the file's content as a raw Base64-encoded string (e.g., "/9j/4AAQSkZJRg...")
 * @throws {Error} If the file cannot be read or converted.
 *
 * @example
 * const file = new File(["Hello, world!"], "hello.txt", { type: "text/plain" });
 * const { dataUrl, rawBase64 } = await convertToBase64AndRaw(file);
 * console.log(dataUrl); // "data:text/plain;base64,SGVsbG8sIHdvcmxkIQ=="
 * console.log(rawBase64); // "SGVsbG8sIHdvcmxkIQ=="
 */
export const convertToBase64AndRaw = (
  file: File
): Promise<{ dataUrl: string; rawBase64: string }> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) {
        const rawBase64 = btoa(
          new Uint8Array(reader.result).reduce(
            (data, byte) => data + String.fromCharCode(byte),
            ""
          )
        );
        const dataUrl = `data:${file.type};base64,${rawBase64}`;
        resolve({ dataUrl, rawBase64 });
      } else {
        reject(new Error("Failed to read file"));
      }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
};
