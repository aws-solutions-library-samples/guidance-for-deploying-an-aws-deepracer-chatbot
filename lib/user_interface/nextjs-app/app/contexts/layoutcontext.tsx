import { FlashbarProps } from "@cloudscape-design/components";
import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

// Types
interface LayoutConfigType {
  readonly navigationHide: boolean;
  readonly helpHide: boolean;
  readonly helpPanelContent: JSX.Element;
  readonly notifications: ReadonlyArray<FlashbarProps.MessageDefinition>;
}

interface LayoutConfigContextType {
  readonly layoutConfig: LayoutConfigType;
  setLayoutConfig: React.Dispatch<React.SetStateAction<LayoutConfigType>>;
  addNotification: (messageDefinition: FlashbarProps.MessageDefinition) => void;
  dismissNotification: (id: string) => void;
  addHelp: (content: JSX.Element) => void;
}

interface LayoutProviderProps {
  children: React.ReactNode;
}

// Constants
const DEFAULT_LAYOUT_CONFIG: LayoutConfigType = Object.freeze({
  navigationHide: true,
  helpHide: true,
  helpPanelContent: <div>Default help text</div>,
  notifications: [],
});

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
export const LayoutProvider: React.FC<LayoutProviderProps> = ({ children }) => {
  const [layoutConfig, setLayoutConfig] = useState<LayoutConfigType>(
    DEFAULT_LAYOUT_CONFIG
  );
  const layoutConfigRef = useRef(layoutConfig);
  layoutConfigRef.current = layoutConfig;

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

  const addHelp = useCallback((content: JSX.Element) => {
    setLayoutConfig((currentState) => {
      if (currentState.helpPanelContent === content) {
        return currentState;
      }

      return {
        ...currentState,
        helpPanelContent: content,
      };
    });
  }, []);

  const contextValue = useMemo(
    () => ({
      layoutConfig,
      setLayoutConfig,
      addNotification,
      dismissNotification,
      addHelp,
    }),
    [layoutConfig, addNotification, dismissNotification, addHelp]
  );

  return (
    <LayoutContext.Provider value={contextValue}>
      {children}
    </LayoutContext.Provider>
  );
};

// Export types and context
export { LayoutContext };
export type { LayoutConfigContextType, LayoutConfigType };
