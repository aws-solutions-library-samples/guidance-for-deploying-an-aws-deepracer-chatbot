import { Authenticator, useAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { ContentLayout, Header } from "@cloudscape-design/components";
import { memo, useCallback, useEffect, useMemo } from "react";
import { useLayoutContext } from "../../contexts/layoutcontext";

/**
 * Represents a notification object in the layout configuration
 */
interface Notification {
  readonly id: string;
  readonly type: "success" | "warning" | "error" | "info";
  readonly content: string;
  readonly dismissible?: boolean;
}

/**
 * Configuration interface for the layout components
 */
interface LayoutConfig {
  /** Controls the visibility of the navigation component */
  readonly navigationHide: boolean;
  /** Controls the visibility of the help panel */
  readonly helpHide: boolean;
  /** Content to be displayed in the help panel */
  readonly helpPanelContent: React.ReactElement;
  /** Array of notification objects to be displayed */
  readonly notifications: readonly Notification[];
}

/**
 * Base props interface for components wrapped with withAuth
 */
interface WithAuthProps {
  /** Add any common props that should be available to all authenticated components */
}

/**
 * Authentication component with sign-in form
 */
const AuthenticationForm = memo(() => (
  <ContentLayout header={<Header variant="h1">Sign In</Header>}>
    <Authenticator
      hideSignUp={true}
      loginMechanisms={["email"]}
      signUpAttributes={["email"]}
    />
  </ContentLayout>
));

AuthenticationForm.displayName = "AuthenticationForm";

/**
 * Higher-order component that adds authentication protection to a component
 * @template P - Props type extending WithAuthProps
 * @param WrappedComponent - Component to be wrapped with authentication
 * @returns Authenticated component
 */
const withAuth = <P extends WithAuthProps>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> => {
  const AuthComponent: React.FC<P> = (props) => {
    const { layoutConfig, setLayoutConfig } = useLayoutContext();
    const { authStatus } = useAuthenticator();
    const isAuthenticated = authStatus === "authenticated";

    // Memoize the layout config calculation
    const getLayoutConfig = useMemo(
      () => ({
        navigationHide: !isAuthenticated,
        helpHide: !isAuthenticated,
        helpPanelContent: layoutConfig.helpPanelContent,
        notifications: layoutConfig.notifications,
      }),
      [
        isAuthenticated,
        layoutConfig.helpPanelContent,
        layoutConfig.notifications,
      ]
    );

    const updateLayoutConfig = useCallback(() => {
      setLayoutConfig(getLayoutConfig);
    }, [getLayoutConfig, setLayoutConfig]);

    useEffect(() => {
      updateLayoutConfig();
      // Cleanup function to prevent memory leaks
      return () => {
        // Reset layout config when component unmounts
        if (isAuthenticated) {
          setLayoutConfig({
            ...layoutConfig,
            navigationHide: true,
            helpHide: true,
          });
        }
      };
    }, [updateLayoutConfig, isAuthenticated, layoutConfig, setLayoutConfig]);

    if (!isAuthenticated) {
      return <AuthenticationForm />;
    }

    return <WrappedComponent {...props} />;
  };

  // Set display name for better debugging
  AuthComponent.displayName = `WithAuth(${
    WrappedComponent.displayName || WrappedComponent.name || "Component"
  })`;

  return memo(AuthComponent);
};

export type { LayoutConfig, Notification, WithAuthProps };
export default withAuth;
