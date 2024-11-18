"use client";

import { Authenticator } from "@aws-amplify/ui-react";
import { AppLayout, Flashbar } from "@cloudscape-design/components";
import "@cloudscape-design/global-styles/dark-mode-utils.css";
import "@cloudscape-design/global-styles/index.css";
import { Amplify } from "aws-amplify";
import { useRouter } from "next/navigation";
import React, { useCallback } from "react";
import Breadcrumbs from "./components/layout/breadcrumbs";
import SideNavigationWrapper from "./components/layout/sideNavigation";
import HelpPanelContent from "./components/layout/helpPanel";
import TopNav from "./components/layout/topNav";
import { LayoutProvider, useLayoutContext } from "./contexts/layoutcontext";

import "./styles.css";

// Move this to a separate file that runs on app initialization
import awsconfig from "./aws-exports.js";
Amplify.configure(awsconfig);

const ariaLabels = {
  navigation: "Navigation drawer",
  navigationClose: "Close navigation drawer",
  navigationToggle: "Open navigation drawer",
  notifications: "Notifications",
  tools: "Help panel",
  toolsClose: "Close help panel",
  toolsToggle: "Open help panel",
};
const MemoizedSideNavigation = React.memo(SideNavigationWrapper);
const MemoizedBreadcrumbs = React.memo(Breadcrumbs);
const MemoizedHelpPanelContent = HelpPanelContent;

function LayoutContent({ children }: { children: React.ReactNode }) {
  const { layoutConfig } = useLayoutContext();
  const router = useRouter();

  const followLink = useCallback(
    (e: CustomEvent) => {
      e.preventDefault();
      router.push("/");
    },
    [router]
  );

  return (
    <AppLayout
      headerSelector="#top-nav"
      ariaLabels={ariaLabels}
      navigation={<MemoizedSideNavigation />}
      breadcrumbs={<MemoizedBreadcrumbs />}
      notifications={
        <Flashbar
          items={layoutConfig.notifications}
          stackItems={layoutConfig.notifications.length > 3}
        />
      }
      content={children}
      contentType="table"
      toolsHide={layoutConfig.helpHide}
      tools={<MemoizedHelpPanelContent />}
      navigationHide={layoutConfig.navigationHide}
    />
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Authenticator.Provider>
      <LayoutProvider>
        <html lang="en">
          <body>
            <div id="top-nav">
              <TopNav />
            </div>
            <LayoutContent>{children}</LayoutContent>
          </body>
        </html>
      </LayoutProvider>
    </Authenticator.Provider>
  );
}
