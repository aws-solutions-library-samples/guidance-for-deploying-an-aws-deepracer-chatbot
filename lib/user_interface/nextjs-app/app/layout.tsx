"use client";

import { Authenticator } from "@aws-amplify/ui-react";
import {
  AppLayout,
  Flashbar,
  FlashbarProps,
} from "@cloudscape-design/components";
import "@cloudscape-design/global-styles/dark-mode-utils.css";
import "@cloudscape-design/global-styles/index.css";
import { Amplify } from "aws-amplify";
import React from "react";
import awsconfig from "./aws-exports.js";
import Breadcrumbs from "./components/layout/breadcrumbs";
import HelpPanelContent from "./components/layout/helpPanel";
import SideNavigationWrapper from "./components/layout/sideNavigation";
import TopNav from "./components/layout/topNav";
import { LayoutProvider, useLayoutContext } from "./contexts/layoutcontext";
import "./styles.css";

// Initialize Amplify with AWS configuration
Amplify.configure(awsconfig);

/**
 * Application-wide aria label configurations
 */
const ariaLabels = {
  navigation: "Navigation drawer",
  navigationClose: "Close navigation drawer",
  navigationToggle: "Open navigation drawer",
  notifications: "Notifications",
  tools: "Help panel",
  toolsClose: "Close help panel",
  toolsToggle: "Open help panel",
} as const;

/**
 * Props interface for the NotificationsSection component
 */
interface NotificationsSectionProps {
  readonly notifications: readonly FlashbarProps.MessageDefinition[];
  readonly stackItems: boolean;
}

/**
 * Props interface for components that accept children
 */
interface ChildrenProps {
  readonly children: React.ReactNode;
}

// Memoized components to prevent unnecessary re-renders
const MemoizedSideNavigation = React.memo(SideNavigationWrapper);
const MemoizedBreadcrumbs = React.memo(Breadcrumbs);
const MemoizedHelpPanelContent = React.memo(HelpPanelContent);

/**
 * NotificationsSection component handles the display of notification messages
 */
const NotificationsSection: React.FC<NotificationsSectionProps> = ({
  notifications,
  stackItems,
}) => <Flashbar items={[...notifications]} stackItems={stackItems} />;

/**
 * LayoutContent component manages the main application layout structure
 */
const LayoutContent: React.FC<ChildrenProps> = ({ children }) => {
  const { layoutConfig } = useLayoutContext();

  return (
    <AppLayout
      headerSelector="#top-nav"
      ariaLabels={ariaLabels}
      navigation={<MemoizedSideNavigation />}
      breadcrumbs={<MemoizedBreadcrumbs />}
      notifications={
        <NotificationsSection
          notifications={layoutConfig.notifications}
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
};

/**
 * TopNavWrapper component encapsulates the top navigation bar
 */
const TopNavWrapper: React.FC = () => (
  <div id="top-nav">
    <TopNav />
  </div>
);

/**
 * RootLayout is the main layout component for the application
 * It provides authentication and layout context to all child components
 */
export default function RootLayout({ children }: ChildrenProps) {
  return (
    <Authenticator.Provider>
      <LayoutProvider>
        <html lang="en">
          <head>
            <meta charSet="utf-8" />
            <meta
              name="viewport"
              content="width=device-width, initial-scale=1"
            />
            <meta name="description" content="AWS DeepRacer Application" />
          </head>
          <body>
            <TopNavWrapper />
            <LayoutContent>{children}</LayoutContent>
          </body>
        </html>
      </LayoutProvider>
    </Authenticator.Provider>
  );
}
