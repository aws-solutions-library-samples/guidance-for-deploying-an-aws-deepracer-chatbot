"use client";

import { AccountSettings, useAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import {
  Button,
  Container,
  ContentLayout,
  Header,
  Modal,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import withAuth from "../../../components/auth/withAuth";
import { useLayoutContext } from "../../../contexts/layoutcontext";

const help_text: JSX.Element = <div>Delete help</div>;

function Page() {
  const router = useRouter();
  const { user } = useAuthenticator((context) => [context.user]);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const { addHelp } = useLayoutContext();
  const [hasLoaded, setHasLoaded] = useState(false);
  useEffect(() => {
    if (hasLoaded) {
      addHelp(help_text);
    } else {
      setHasLoaded(true);
    }
  }, [hasLoaded]);

  const handleSuccess = useCallback(() => {
    console.log("User Deleted");
    setIsDeleting(false);
    router.push("/");
  }, [router]);

  const handleError = useCallback((error: Error) => {
    console.error("Failed to delete user:", error);
    setIsDeleting(false);
    // TODO: Show error message to user
  }, []);

  const username = useMemo(() => user?.username ?? "", [user]);

  const handleDeleteClick = useCallback(() => {
    setShowConfirmation(true);
  }, []);

  const handleConfirmDelete = useCallback(() => {
    setShowConfirmation(false);
    setIsDeleting(true);
  }, []);

  return (
    <ContentLayout header={<Header variant="h1">User Profile</Header>}>
      <SpaceBetween direction="vertical" size="s">
        <Container header={<Header variant="h2">Delete Account</Header>}>
          <Header variant="h3">{username}</Header>
          <Button onClick={handleDeleteClick}>Delete Account</Button>
          {isDeleting && (
            <AccountSettings.DeleteUser
              onSuccess={handleSuccess}
              onError={handleError}
            />
          )}
        </Container>
      </SpaceBetween>
      <Modal
        visible={showConfirmation}
        onDismiss={() => setShowConfirmation(false)}
        header="Confirm Account Deletion"
      >
        Are you sure you want to delete your account? This action cannot be
        undone.
        <Button onClick={handleConfirmDelete}>Confirm Delete</Button>
      </Modal>
    </ContentLayout>
  );
}

export default withAuth(Page);
