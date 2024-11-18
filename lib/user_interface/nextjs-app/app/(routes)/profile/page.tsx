"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import {
  Button,
  Container,
  ContentLayout,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
} from "@cloudscape-design/components";
import { updatePassword } from "aws-amplify/auth";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import withAuth from "../../components/auth/withAuth";
import { useLayoutContext } from "../../contexts/layoutcontext";
import usePasswordForm from "../../hooks/usePasswordForm";

const help_text: JSX.Element = <div>Profile help</div>;

function Page() {
  const router = useRouter();
  const { user, signOut } = useAuthenticator((context) => [
    context.user,
    context.signOut,
  ]);
  const {
    currentPassword,
    setCurrentPassword,
    newPassword,
    setNewPassword,
    newPasswordConfirm,
    setNewPasswordConfirm,
    isFormValid,
    newPasswordErrorMessage,
    clearFields,
  } = usePasswordForm();

  const { addHelp, addNotification, dismissNotification } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  const handleSignOut = useCallback(async () => {
    await signOut();
    router.push("/");
  }, [signOut, router]);

  const handleUpdatePassword = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault(); // Prevent default form submission
      try {
        await updatePassword({ newPassword, oldPassword: currentPassword });
        clearFields();
        addNotification({
          type: "success",
          dismissible: true,
          content: `Password updated`,
          id: "pwdUpdateNotification",
          onDismiss: () => dismissNotification("pwdUpdateNotification"),
        });
      } catch (error) {
        addNotification({
          type: "error",
          dismissible: true,
          content: `Failed to update password: ${error}`,
          id: "errorNotification",
          onDismiss: () => dismissNotification("errorNotification"),
        });
      }
    },
    [newPassword, currentPassword, clearFields]
  );

  const username = user?.signInDetails?.loginId ?? "";

  return (
    <ContentLayout header={<Header variant="h1">User Profile</Header>}>
      <SpaceBetween direction="vertical" size="s">
        <Container header={<Header variant="h2">User details</Header>}>
          <Header variant="h3">{username}</Header>
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="primary" onClick={handleSignOut}>
              Sign out
            </Button>
            <Button
              variant="normal"
              onClick={() => router.push("/profile/delete")}
            >
              Delete Account
            </Button>
          </SpaceBetween>
        </Container>

        <Container header={<Header variant="h2">Change password</Header>}>
          <form onSubmit={handleUpdatePassword}>
            <Form
              actions={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button
                    formAction="none"
                    variant="link"
                    onClick={clearFields}
                  >
                    Reset
                  </Button>
                  <Button variant="primary" disabled={!isFormValid}>
                    Update password
                  </Button>
                </SpaceBetween>
              }
            >
              <SpaceBetween direction="vertical" size="l">
                <FormField label="Current password">
                  <Input
                    value={currentPassword}
                    placeholder="Current password"
                    type="password"
                    onChange={(e) => setCurrentPassword(e.detail.value)}
                  />
                </FormField>

                <FormField
                  label="New password"
                  errorText={newPasswordErrorMessage}
                >
                  <Input
                    value={newPassword}
                    placeholder="New password"
                    type="password"
                    onChange={(e) => setNewPassword(e.detail.value)}
                  />
                </FormField>

                <FormField
                  label="Confirm new password"
                  errorText={newPasswordErrorMessage}
                >
                  <Input
                    value={newPasswordConfirm}
                    placeholder="Confirm new password"
                    type="password"
                    onChange={(e) => setNewPasswordConfirm(e.detail.value)}
                  />
                </FormField>
              </SpaceBetween>
            </Form>
          </form>
        </Container>
      </SpaceBetween>
    </ContentLayout>
  );
}

export default withAuth(Page);
