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

const help_text: JSX.Element = <div>home help</div>;
function Page() {
  const { addHelp, layoutConfig, setLayoutConfig } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  return (
    <ContentLayout header={<Header variant="h1">Home</Header>}>
      <Container>
        <Header variant="h1">DeepRacer Chatbot</Header>
        <Cards
          ariaLabels={{
            itemSelectionLabel: (e, t) => `select ${t.name}`,
            selectionGroupLabel: "Item selection",
          }}
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
          cardsPerRow={[{ cards: 1 }, { minWidth: 800, cards: 4 }]}
          className="homepage_cards"
          items={[
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
          ]}
        />
      </Container>
    </ContentLayout>
  );
}

Page.displayName = "HomePage";

export default withAuth(Page);
