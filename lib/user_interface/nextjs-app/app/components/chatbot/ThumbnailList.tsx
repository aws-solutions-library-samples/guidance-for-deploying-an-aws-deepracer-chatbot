import { FC } from "react";

interface ThumbnailListProps {
  thumbnails: string[];
}

const ThumbnailList: FC<ThumbnailListProps> = ({ thumbnails }) => {
  return (
    <ul style={{ listStyle: "none", padding: 0 }}>
      {thumbnails.map((thumbnail, index) => (
        <li key={index} style={{ display: "inline-block", marginRight: "8px" }}>
          <img
            src={thumbnail}
            alt={`Thumbnail ${index + 1}`}
            style={{ maxWidth: "100px", maxHeight: "100px", padding: "0 0 0 40px" }}
          />
        </li>
      ))}
    </ul>
  );
};

export default ThumbnailList;
