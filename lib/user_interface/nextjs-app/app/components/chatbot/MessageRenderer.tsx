import React from "react";
import ReactMarkdown from "react-markdown";
import "./MessageRenderer.css";

interface MessageRendererProps {
  children?: string;
}

const MessageRenderer: React.FC<MessageRendererProps> = React.memo(
  ({ children }) => {
    return (
      <div className="markdown-content">
        <ReactMarkdown>{children ?? ""}</ReactMarkdown>
      </div>
    );
  }
);

MessageRenderer.displayName = "MessageRenderer";

export default MessageRenderer;
