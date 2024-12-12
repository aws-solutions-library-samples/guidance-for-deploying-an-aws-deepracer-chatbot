import React from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import "./MessageRenderer.css";

interface MessageRendererProps {
  text: string;
}

const MessageRenderer: React.FC<MessageRendererProps> = React.memo(
  ({ text }) => {
    // Function to normalize text content
    const normalizeText = (content: string) => {
      return content
        .replace(/\s+/g, " ") // Replace multiple spaces with single space
        .trim(); // Remove leading/trailing whitespace
    };

    return (
      <div className="markdown-content">
        <ReactMarkdown
          components={{
            code({ className, children }) {
              const match = /language-(\w+)/.exec(className || "");
              const content = String(children).replace(/\n$/, "");

              return match ? (
                <SyntaxHighlighter
                  PreTag="div"
                  language={match[1]}
                  //style={dark}
                >
                  {content}
                </SyntaxHighlighter>
              ) : (
                <code className={className}>{content}</code>
              );
            },
          }}
        >
          {text}
        </ReactMarkdown>
      </div>
    );
  }
);

MessageRenderer.displayName = "MessageRenderer";

export default MessageRenderer;
