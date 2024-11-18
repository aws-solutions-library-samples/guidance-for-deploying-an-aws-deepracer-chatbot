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
    <h5>Prepare your AWS DeepRacer model</h5>
    <ul>
      <li>
        Export your DeepRacer model from the AWS DeepRacer console to your local
        machine.
      </li>
      <li>
        Ensure you have the model's reward function, training logs, metadata,
        evaluation logs, hyperparameters, and action space.
      </li>
    </ul>
    <h5>Upload your model</h5>
    <ul>
      <li>
        Navigate to the "Manage Models" page in the side navigation on the left
        hand side
      </li>
      <li>Upload your exported DeepRacer model files as a zip file.</li>
      <li>
        The model will be processed into format suitable for analysis by an LLM
      </li>
    </ul>
    <h5>Ask a question</h5>
    <ul>
      <li>
        Formulate a question about your DeepRacer model, its performance, or
        potential improvements.
      </li>
      <li>
        Include any relevant images of DeepRacer tracks, training graphs, or
        evaluation jobs.
      </li>
      <li>Provide the name of the model you want to analyze.</li>
    </ul>
    <h5>AI analysis</h5>
    <ul>
      <li>The AI assistant will analyze your model using the provided data</li>
      <li>
        It will consider factors like reward score trends, overfitting, and
        algorithm choices, action space and reward function strategy.
      </li>
    </ul>
    <h5>Follow the suggestions</h5>
    <ul>
      <li>
        Use the provided step-by-step instructions to implement changes in the
        AWS DeepRacer console.
      </li>
    </ul>
    <h5>Ask follow-up questions</h5>
    <ul>
      <li>
        If needed, ask additional questions for clarification or further
        analysis.
      </li>
      <li>The AI will consider the conversation history for context.</li>
    </ul>
    <h5>Iterate and improve</h5>
    <ul>
      <li>
        Apply the suggested changes to your model. - Retrain and evaluate your
        model as needed.
      </li>
      <li>Repeat the process to continue refining your DeepRacer model.</li>
    </ul>
  </div>
);

function Page() {
  // Use useMemo to generate sessionId once and memoize it
  const sessionId = useMemo(() => uuidv4(), []);
  const { addHelp } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  const default_prompts: string[] = [
    "Given the reward function is looking to follow the centre line, provide improvements and suggestions",
    "Which hyperparameters should I change with this model to improve it?",
  ];

  return (
    <ContentLayout header={<Header variant="h1">Model Evaluation</Header>}>
      <ChatWindow
        chatbotType={ChatbotVariant.modelEvaluation}
        sessionId={sessionId}
        defaultPrompts={default_prompts}
      />
    </ContentLayout>
  );
}

export default withAuth(Page);
