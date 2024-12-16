"use client";

import { HelpPanel } from "@cloudscape-design/components";
import { useLayoutContext } from "../../contexts/layoutcontext";

function HelpPanelContent() {
  const { layoutConfig } = useLayoutContext();

  return (
    <HelpPanel header={<h2>Help</h2>}>
      {layoutConfig?.helpPanelContent || <p>No help content available</p>}
    </HelpPanel>
  );
}

// Do not memoize - we want it to re-render whenever needed
export default HelpPanelContent;
