"use client";

import SideNavigation, {
  SideNavigationProps,
} from "@cloudscape-design/components/side-navigation";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";
import { GetModelsQuery } from "../../API";
import { useModels } from "../../hooks/useModel";

// Navigation configuration
const DEFAULT_ITEMS: SideNavigationProps["items"] = [
  { type: "link", text: "Home", href: "/" },
  { type: "divider" },
  {
    type: "section-group",
    title: "Chatbots",
    items: [
      { type: "link", text: "Q&A", href: "/questionandanswer" },
      {
        type: "link",
        text: "Reward Function Generation",
        href: "/rewardfunction",
      },
      { type: "link", text: "Model Evaluation", href: "/modeleval" },
    ],
  },
  { type: "divider" },
  {
    type: "section-group",
    title: "DeepRacer models",
    items: [{ type: "link", text: "Manage models", href: "/manageModels" }],
  },
  { type: "divider" },
];

// Helper function to generate model navigation items
const getModelItems = (
  models: GetModelsQuery["getModels"]
): SideNavigationProps["items"] => {
  const availableModels =
    models
      ?.filter((model) => model?.status !== "error")
      .map((model) => ({
        type: "link" as const,
        text: model?.modelName ?? "",
        href: `/models/${model?.modelName}`, // Added proper link structure
      })) ?? [];

  return [
    ...DEFAULT_ITEMS,
    {
      type: "section-group",
      title: "Available models",
      items: availableModels,
    },
  ];
};

export default function SideNavigationWrapper() {
  const router = useRouter();
  const pathname = usePathname();
  const { models } = useModels();

  // Generate navigation items
  const items = useMemo(() => getModelItems(models), [models]);

  // Handle navigation
  const handleFollow = useCallback(
    (event: CustomEvent<SideNavigationProps.FollowDetail>) => {
      if (!event.detail.external) {
        event.preventDefault();
        router.push(event.detail.href);
      }
    },
    [router]
  );

  return (
    <SideNavigation
      activeHref={pathname}
      onFollow={handleFollow}
      items={items}
    />
  );
}
