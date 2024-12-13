"use client";

import { FlashbarProps } from "@cloudscape-design/components";
import React, { createContext, useCallback, useContext, useState } from "react";

// Types
interface LayoutConfigType {
  readonly navigationHide: boolean;
  readonly helpHide: boolean;
  readonly helpPanelContent: JSX.Element | null;
  readonly notifications: ReadonlyArray<FlashbarProps.MessageDefinition>;
}

interface LayoutConfigContextType {
  readonly layoutConfig: LayoutConfigType;
  setLayoutConfig: React.Dispatch<React.SetStateAction<LayoutConfigType>>;
  addNotification: (messageDefinition: FlashbarProps.MessageDefinition) => void;
  dismissNotification: (id: string) => void;
  addHelp: (content: JSX.Element | null) => void;
}

interface LayoutProviderProps {
  children: React.ReactNode;
}

// Constants
const DEFAULT_LAYOUT_CONFIG: LayoutConfigType = {
  navigationHide: true,
  helpHide: false, // Set to false to show the help panel by default
  helpPanelContent: null, // Will be set by pages
  notifications: [],
};

// Context Creation
const LayoutContext = createContext<LayoutConfigContextType | null>(null);

// Utility functions
const updateNotifications = (
  currentNotifications: ReadonlyArray<FlashbarProps.MessageDefinition>,
  newNotification: FlashbarProps.MessageDefinition
): ReadonlyArray<FlashbarProps.MessageDefinition> => {
  const index = currentNotifications.findIndex(
    (notification) => notification.id === newNotification.id
  );

  if (index > -1) {
    return Object.freeze([
      ...currentNotifications.slice(0, index),
      newNotification,
      ...currentNotifications.slice(index + 1),
    ]);
  }

  return Object.freeze([...currentNotifications, newNotification]);
};

// Custom hook for using the context
export const useLayoutContext = (): LayoutConfigContextType => {
  const context = useContext(LayoutContext);

  if (!context) {
    throw new Error("useLayoutContext must be used within a LayoutProvider");
  }

  return context;
};

// Main Provider Component
export function LayoutProvider({ children }: LayoutProviderProps) {
  const [layoutConfig, setLayoutConfig] = useState<LayoutConfigType>(
    DEFAULT_LAYOUT_CONFIG
  );

  const addNotification = useCallback(
    (messageDefinition: FlashbarProps.MessageDefinition) => {
      setLayoutConfig((currentState) => ({
        ...currentState,
        notifications: updateNotifications(
          currentState.notifications,
          messageDefinition
        ),
      }));
    },
    []
  );

  const dismissNotification = useCallback((id: string) => {
    setLayoutConfig((currentState) => {
      const { notifications } = currentState;
      const notificationExists = notifications.some(
        (notification) => notification.id === id
      );

      if (!notificationExists) {
        return currentState;
      }

      return {
        ...currentState,
        notifications: Object.freeze(
          notifications.filter((notification) => notification.id !== id)
        ),
      };
    });
  }, []);

  // Add help content to layout config with improved validation, state management and debouncing
  const addHelp = useCallback((content: JSX.Element | null) => {
    const timestamp = new Date().toISOString();

    // Debounce the state update to avoid race conditions
    // and batch multiple rapid changes together
    const updateState = () => {
      setLayoutConfig((prev) => {
        // Only update if content has actually changed
        if (prev.helpPanelContent === content) {
          return prev;
        }

        // Hide panel when clearing content or show it when setting new content
        const newHelpHide = content === null;

        const newState = {
          ...prev,
          helpHide: newHelpHide,
          helpPanelContent: content,
        };

        return newState;
      });
    };

    // Use requestAnimationFrame to ensure DOM updates are synchronized
    // and avoid potential race conditions during page transitions
    // Cancel any pending animation frames
    const frameId = requestAnimationFrame(updateState);

    // Return cleanup function to cancel animation frame if component unmounts
    return () => {
      cancelAnimationFrame(frameId);
    };
  }, []);

  // Create fresh context value each time to ensure updates propagate
  const contextValue = {
    layoutConfig,
    setLayoutConfig,
    addNotification,
    dismissNotification,
    addHelp,
  };

  return (
    <LayoutContext.Provider value={contextValue}>
      {children}
    </LayoutContext.Provider>
  );
}

// Export types and context
export { LayoutContext };
export type { LayoutConfigContextType, LayoutConfigType };
