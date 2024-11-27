/**
 * @fileoverview Higher-order component for handling authentication and layout configuration
 */

import { Authenticator, useAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { ContentLayout, Header } from "@cloudscape-design/components";
import { memo, useCallback, useEffect } from "react";
import {
  LayoutConfigType,
  useLayoutContext,
} from "../../contexts/layoutcontext";

/**
 * Base props interface for components that can be wrapped with authentication
 * @interface WithAuthProps
 */
interface WithAuthProps {
  className?: string;
  id?: string;
}

/**
 * Props interface for the AuthComponent
 * @interface AuthComponentProps
 * @template P - Component props type extending WithAuthProps
 */
interface AuthComponentProps<P extends WithAuthProps> {
  /** Component to be wrapped with authentication */
  WrappedComponent: React.ComponentType<P>;
  /** Props to be passed to the wrapped component */
  componentProps: P;
}

/**
 * Generates layout configuration based on authentication status
 * @param {boolean} isAuthenticated - Current authentication status
 * @param {LayoutConfigType} currentConfig - Current layout configuration
 * @returns {LayoutConfigType} Updated layout configuration
 */
const getLayoutConfig = (
  isAuthenticated: boolean,
  currentConfig: LayoutConfigType
): LayoutConfigType => ({
  navigationHide: !isAuthenticated,
  helpHide: !isAuthenticated,
  helpPanelContent: currentConfig.helpPanelContent,
  notifications: currentConfig.notifications,
});

/**
 * Component that handles authentication state and layout configuration
 * @template P - Component props type extending WithAuthProps
 * @param {AuthComponentProps<P>} props - Component props
 * @returns {JSX.Element} Rendered component
 */
const AuthComponent = <P extends WithAuthProps>({
  WrappedComponent,
  componentProps,
}: AuthComponentProps<P>) => {
  const { layoutConfig, setLayoutConfig } = useLayoutContext();
  const { authStatus } = useAuthenticator((context) => [context.authStatus]);

  const isAuthenticated = authStatus === "authenticated";

  /**
   * Updates layout configuration based on authentication status
   * Memoized to prevent unnecessary re-renders
   */
  const updateLayoutConfig = useCallback(() => {
    try {
      setLayoutConfig((currentConfig) => {
        const newConfig = getLayoutConfig(isAuthenticated, currentConfig);
        // Only update if there are actual changes
        if (
          currentConfig.navigationHide === newConfig.navigationHide &&
          currentConfig.helpHide === newConfig.helpHide
        ) {
          return currentConfig;
        }
        return newConfig;
      });
    } catch (error) {
      console.error("Error updating layout configuration:", error);
    }
  }, [isAuthenticated, setLayoutConfig]);

  // Update layout config when auth status changes
  useEffect(() => {
    updateLayoutConfig();
  }, [authStatus, updateLayoutConfig]);

  // Show authentication UI if user is not authenticated
  if (!isAuthenticated) {
    return (
      <ContentLayout header={<Header variant="h1">Sign In</Header>}>
        <Authenticator
          hideSignUp={true}
          loginMechanisms={["email"]}
          signUpAttributes={["email"]}
        />
      </ContentLayout>
    );
  }

  return <WrappedComponent {...componentProps} />;
};

/**
 * Higher-order component that adds authentication and layout management
 * to a component
 *
 * @template P - Component props type extending WithAuthProps
 * @param {React.ComponentType<P>} WrappedComponent - Component to wrap with authentication
 * @returns {React.FC<P>} Wrapped component with authentication
 *
 * @example
 * // Wrap a component with authentication
 * const MyProtectedComponent = withAuth(MyComponent);
 *
 * // Use the protected component
 * function App() {
 *   return <MyProtectedComponent someProp="value" />;
 * }
 */
const withAuth = <P extends WithAuthProps>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> => {
  const WithAuthWrapper: React.FC<P> = (props) => (
    <AuthComponent<P>
      WrappedComponent={WrappedComponent}
      componentProps={props}
    />
  );

  // Set display name for debugging purposes
  WithAuthWrapper.displayName = `WithAuth(${
    WrappedComponent.displayName || WrappedComponent.name || "Component"
  })`;

  return memo(WithAuthWrapper);
};

export default withAuth;
