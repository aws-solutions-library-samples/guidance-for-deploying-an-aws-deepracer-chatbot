"use client";

import {
    HelpPanel
} from "@cloudscape-design/components";
import React from "react";
import { useLayoutContext } from "../../contexts/layoutcontext";

export default function HelpPanelContent() {
  const { layoutConfig } = useLayoutContext();
  return (
    <HelpPanel header="Help" footer="">
      <div>
        { layoutConfig.helpPanelContent }
      </div>
    </HelpPanel>
  );
}
