"use client";

import {
  Cards,
  Container,
  ContentLayout,
  Header,
} from "@cloudscape-design/components";
import { useEffect, useState } from "react";
import withAuth from "./components/auth/withAuth";
import { useLayoutContext } from "./contexts/layoutcontext";

// Define the type for card items
type CardItem = {
  link: string;
  name: string;
  description: string;
};

// Constants
const HELP_TEXT: JSX.Element = (
  <div>
    <h2>Welcome to DeepRacer Chatbot</h2>
    <p>Select a card to get started with your DeepRacer journey.</p>
  </div>
);

const CARD_ITEMS: readonly CardItem[] = [
  {
    link: "questionandanswer",
    name: "Question & Answers",
    description:
      "Chat your way to knowledge with interactive learning which helps you excel at AWS DeepRacer",
  },
  {
    link: "rewardfunction",
    name: "Reward Function",
    description:
      "Chat your way to optimized reward functions and improve your DeepRacer model's performance",
  },
  {
    link: "modeleval",
    name: "Model Evaluation",
    description:
      "Analyze your DeepRacer model's performance metrics and get AI-powered insights to enhance your racing",
  },
  {
    link: "manageModels",
    name: "Manage Models",
    description:
      "Upload and organize your pre-trained DeepRacer models to enable AI-powered analysis and evaluation features",
  },
] as const;

const CARDS_PER_ROW = [{ cards: 1 }, { minWidth: 800, cards: 4 }];

const ARIA_LABELS = {
  itemSelectionLabel: (_e: unknown, t: CardItem) => `select ${t.name}`,
  selectionGroupLabel: "Item selection",
};

function Page() {
  const { addHelp } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);

  useEffect(() => {
    if (!hasLoaded) {
      setHasLoaded(true);
      return;
    }
    addHelp(HELP_TEXT);
  }, [hasLoaded, addHelp]);

  return (
    <ContentLayout header={<Header variant="h1">Home</Header>}>
      <Container>
        <Header variant="h1">DeepRacer Chatbot</Header>
        <Cards
          ariaLabels={ARIA_LABELS}
          cardDefinition={{
            header: (item) => <h4>{item.name}</h4>,
            sections: [
              {
                id: "usage",
                header: "Usage",
                content: (item) => item.description,
              },
            ],
          }}
          cardsPerRow={CARDS_PER_ROW}
          className="homepage_cards"
          items={CARD_ITEMS}
        />
      </Container>
    </ContentLayout>
  );
}

Page.displayName = "HomePage";

export default withAuth(Page);
