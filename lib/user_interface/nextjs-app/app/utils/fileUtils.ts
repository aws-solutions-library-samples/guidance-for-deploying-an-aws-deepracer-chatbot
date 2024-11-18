import path from "path";

export const fileNameWithoutExtension = (fileName: string): string => {
  const ext = path.extname(fileName);
  let baseName = path.basename(fileName, ext);

  if (ext === ".gz") {
    baseName = path.basename(baseName, ".tar");
  }

  return baseName;
};
