import { Authenticator, useAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { ContentLayout, Header } from "@cloudscape-design/components";
import { useEffect } from "react";
import { useLayoutContext } from "../../contexts/layoutcontext";

type WithAuthProps = {
  // Define the common props shared by all components wrapped by withAuth.
};

const withAuth = <P extends WithAuthProps>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> => {
  const Auth: React.FC<P> = (props) => {
    const { layoutConfig, setLayoutConfig } = useLayoutContext();
    const { authStatus } = useAuthenticator((context) => [context.authStatus]);

    useEffect(() => {
      if (authStatus !== "authenticated") {
        setLayoutConfig({
          navigationHide: true,
          helpHide: true,
          helpPanelContent: layoutConfig.helpPanelContent,
          notifications: layoutConfig.notifications,
        });
      } else {
        setLayoutConfig({
          navigationHide: false,
          helpHide: false,
          helpPanelContent: layoutConfig.helpPanelContent,
          notifications: layoutConfig.notifications,
        });
      }
    }, [authStatus]);

    if (authStatus !== "authenticated") {
      return (
        <ContentLayout header={<Header variant="h1">Sign In</Header>}>
          <Authenticator
            hideSignUp={true}
            loginMechanisms={["email"]}
            signUpAttributes={["email"]}
          ></Authenticator>
        </ContentLayout>
      );
    } else {
      return <WrappedComponent {...props} />;
    }
  };
  return Auth;
};

export default withAuth;
