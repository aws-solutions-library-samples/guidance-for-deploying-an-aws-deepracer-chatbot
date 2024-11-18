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
      <h5>Describe Your Needs</h5>
      <ul>
        <li>Type your request in the text box below.</li>
        <li>Explain the behavior you want for your DeepRacer.</li>
        <li>Mention any specific track features you're targeting.</li>
      </ul>

      <h5>Provide Details (if applicable)</h5>
      <ul>
        <li>Track type: oval, S-curve, complex, etc.</li>
        <li>Custom action space: steering and speed ranges.</li>
        <li>Challenging sections of the track.</li>
      </ul>

      <h5>Submit Your Request</h5>
      <ul>
        <li>Click the send button or press Enter.</li>
      </ul>

      <h5>Review the AI-Generated Function</h5>
      <ul>
        <li>Examine the Python code provided.</li>
        <li>Read the beginner-friendly explanation.</li>
      </ul>

      <h5>Refine Your Function</h5>
      <ul>
        <li>Ask for modifications if needed.</li>
        <li>The AI will consider your previous requests.</li>
      </ul>

      <h5>Tips for Better Results</h5>
      <ul>
        <li>Be specific about desired behaviors.</li>
        <li>Mention any previous training issues.</li>
        <li>Ask for explanations if anything is unclear.</li>
      </ul>
    </div>
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
    "Write me a reward function that follows the centre line",
    "Write me a reward function to follow waypoints",
  ];

  return (
    <ContentLayout
      header={<Header variant="h1">Reward Function Generation</Header>}
    >
      <ChatWindow
        chatbotType={ChatbotVariant.rewardFunctionGeneration}
        sessionId={sessionId}
        defaultPrompts={default_prompts}
      />
    </ContentLayout>
  );
}

export default withAuth(Page);
