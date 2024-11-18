"use client";

import { ContentLayout, Header } from "@cloudscape-design/components";
import { useEffect, useMemo, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { ChatbotVariant } from "../../API";
import withAuth from "../../components/auth/withAuth";
import ChatWindow from "../../components/chatbot/ChatWindow";
import { useLayoutContext } from "../../contexts/layoutcontext";

const help_text: JSX.Element = (
  <div>
    <div>
      <h5>Ask a Question about AWS DeepRacer</h5>
      <ul>
        <li>Type your question in the text box at the bottom of the page.</li>
        <li>Click the send button or press Enter to submit your question.</li>
      </ul>

      <h5>Explore Example Questions</h5>
      <ul>
        <li>
          Click on the example prompts provided to quickly ask common questions.
        </li>
      </ul>

      <h5>Receive AI-Powered Answers</h5>
      <ul>
        <li>
          The AI assistant will analyze your question and provide a detailed
          response.
        </li>
        <li>
          Answers are based on official AWS DeepRacer documentation and best
          practices.
        </li>
      </ul>

      <h5>Get Explanations and Next Steps</h5>
      <ul>
        <li>
          Each answer includes a beginner-friendly explanation of the topic.
        </li>
        <li>
          The AI will provide clear, actionable steps you can take in the AWS
          DeepRacer console.
        </li>
      </ul>

      <h5>Ask Follow-up Questions</h5>
      <ul>
        <li>If you need more information, simply ask another question.</li>
        <li>
          The AI assistant will consider the conversation history for context.
        </li>
      </ul>

      <h5>Focus on AWS DeepRacer Console</h5>
      <ul>
        <li>
          All suggestions and instructions are designed to be implemented within
          the AWS DeepRacer console.
        </li>
        <li>
          No external tools or resources are required to follow the AI's advice.
        </li>
      </ul>

      <h5>Improve Your DeepRacer Knowledge</h5>
      <ul>
        <li>
          Use this Q&A feature to learn about various aspects of AWS DeepRacer.
        </li>
        <li>
          Gain insights into model training, evaluation, and optimization
          techniques.
        </li>
      </ul>
    </div>
  </div>
);

function Page() {
  // Use useMemo to generate sessionId once and memoize it
  const sessionId = useMemo(() => uuidv4(), []);
  const { addHelp, layoutConfig, setLayoutConfig } = useLayoutContext();

  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  const default_prompts: string[] = [
    "What is AWS DeepRacer?",
    "What is a reward function?",
    "What is a hyperparameter?",
  ];

  return (
    <ContentLayout header={<Header variant="h1">Q&A</Header>}>
      <ChatWindow
        chatbotType={ChatbotVariant.questionsAndAnswers}
        sessionId={sessionId}
        defaultPrompts={default_prompts}
      />
    </ContentLayout>
  );
}

export default withAuth(Page);
