import { FlashbarProps } from "@cloudscape-design/components";
import React, { createContext, useCallback, useContext } from "react";

export type LayoutConfigType = {
  navigationHide: boolean;
  helpHide: boolean;
  helpPanelContent: JSX.Element;
  notifications: FlashbarProps.MessageDefinition[];
};

export type LayoutConfigContextType = {
  layoutConfig: LayoutConfigType;
  setLayoutConfig: React.Dispatch<React.SetStateAction<LayoutConfigType>>;
  addNotification: (messageDefinition: FlashbarProps.MessageDefinition) => void;
  dismissNotification: (id: string) => void;
  addHelp: (content: JSX.Element) => void;
};

const defaultLayoutConfig: LayoutConfigType = {
  navigationHide: true,
  helpHide: true,
  helpPanelContent: <div>"Default help text"</div>,
  notifications: [],
};

export const LayoutContext = createContext<LayoutConfigContextType | null>(
  null
);

export const useLayoutContext = () => {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error("useLayoutContext must be used within a LayoutProvider");
  }
  return context;
};

export const LayoutProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [layoutConfig, setLayoutConfig] =
    React.useState<LayoutConfigType>(defaultLayoutConfig);

  const addNotification = useCallback(
    (messageDefinition: FlashbarProps.MessageDefinition) => {
      setLayoutConfig((currentState) => {
        const index = currentState.notifications.findIndex(
          (m) => m.id === messageDefinition.id
        );
        const newNotifications = [...currentState.notifications];

        if (index > -1) {
          newNotifications[index] = messageDefinition;
        } else {
          newNotifications.push(messageDefinition);
        }

        const config = { ...currentState, notifications: newNotifications };
        return config;
      });
    },
    []
  );

  const dismissNotification = useCallback((id: string) => {
    setLayoutConfig((currentState) => ({
      ...currentState,
      notifications: currentState.notifications.filter((m) => m.id !== id),
    }));
  }, []);

  const addHelp = useCallback((content: JSX.Element) => {
    setLayoutConfig((currentState) => ({
      ...currentState,
      helpPanelContent: content,
    }));
  }, []);

  const contextValue = React.useMemo(
    () => ({
      layoutConfig,
      setLayoutConfig,
      addNotification,
      dismissNotification,
      addHelp,
    }),
    [
      layoutConfig,
      setLayoutConfig,
      addNotification,
      dismissNotification,
      addHelp,
    ]
  );

  return (
    <LayoutContext.Provider value={contextValue}>
      {children}
    </LayoutContext.Provider>
  );
};
