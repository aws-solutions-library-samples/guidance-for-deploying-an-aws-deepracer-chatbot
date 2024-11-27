"use client";

import { HelpPanel } from "@cloudscape-design/components";
import { FC } from "react";
import { useLayoutContext } from "../../contexts/layoutcontext";

interface HelpPanelContentProps {
  footerContent?: React.ReactNode;
}

export const HelpPanelContent: FC<HelpPanelContentProps> = ({
  footerContent = null,
}) => {
  const { layoutConfig } = useLayoutContext();

  if (!layoutConfig?.helpPanelContent) {
    return null;
  }

  return (
    <HelpPanel header="Help" footer={footerContent}>
      <div className="help-panel-content">{layoutConfig.helpPanelContent}</div>
    </HelpPanel>
  );
};

export default HelpPanelContent;
