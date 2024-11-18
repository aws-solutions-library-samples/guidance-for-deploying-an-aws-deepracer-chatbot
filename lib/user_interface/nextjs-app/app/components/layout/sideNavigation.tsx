"use client";

import SideNavigation, {
  SideNavigationProps,
} from "@cloudscape-design/components/side-navigation";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";
import { GetModelsQuery } from "../../API";
import { useModels } from "../../hooks/useModel";

const DEFAULT_ITEMS: NonNullable<SideNavigationProps["items"]> = [
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

const getModelItems = (
  models: GetModelsQuery["getModels"]
): SideNavigationProps.Item[] => [
  ...DEFAULT_ITEMS,
  {
    type: "section-group",
    title: "Available models",
    items:
      models
        ?.filter((model) => model?.status !== "error")
        .map((model) => ({
          type: "link",
          text: model?.modelName ?? "",
          href: `""`,
        })) ?? [],
  },
];

export default function SideNavigationWrapper() {
  const router = useRouter();
  const pathname = usePathname();
  const { models } = useModels();

  console.info(models);
  const items = useMemo(() => getModelItems(models), [models]);

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
