"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import {
  ButtonDropdownProps,
  TopNavigation,
  TopNavigationProps,
} from "@cloudscape-design/components";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * TopNav Component
 *
 * A top navigation bar component that handles user authentication state and navigation.
 * It displays the application logo, title, and user-specific utilities including a
 * profile dropdown menu when authenticated.
 *
 * Features:
 * - Displays DeepRacer logo and title
 * - Shows user profile dropdown when authenticated
 * - Handles navigation between pages
 * - Manages sign-out functionality
 *
 * @component
 * @returns {JSX.Element} Rendered TopNavigation component
 */
export default function TopNav(): JSX.Element {
  const router = useRouter();

  /**
   * Authentication hook providing user status and controls
   * @type {Object} Authentication context including user status and sign-out function
   */
  const { authStatus, user, signOut } = useAuthenticator((context) => [
    context.user,
  ]);

  /**
   * State for managing navigation utilities (e.g., user profile dropdown)
   * @type {TopNavigationProps.Utility[] | undefined}
   */
  const [utilities, setUtilities] = useState<TopNavigationProps.Utility[]>();

  /**
   * Handles navigation when links are clicked
   * Prevents default behavior and uses Next.js router for navigation
   *
   * @param {CustomEvent} e - The click event from the navigation component
   */
  function followLink(e: CustomEvent): void {
    e.preventDefault();
    const href = (e.target as HTMLAnchorElement).getAttribute("href");
    if (href) {
      router.push(href);
    }
  }

  /**
   * Extracts username from authentication context
   * Falls back to empty string if user is not authenticated
   */
  const username = user?.signInDetails?.loginId ?? "";

  /**
   * Effect to update navigation utilities based on authentication status
   * Creates user profile dropdown menu when user is authenticated
   *
   * Dependencies:
   * - user: Updates when user auth state changes
   * - authStatus: Updates when authentication status changes
   * - username: Updates when username changes
   */
  useEffect(() => {
    const userProfile: TopNavigationProps.Utility = {
      type: "menu-dropdown",
      text: username,
      iconName: "user-profile",
      items: [
        { id: "profile", text: "Profile" },
        { id: "signout", text: "Sign out" },
      ],
      onItemClick: ({ detail }) => {
        detail.id === "signout" ? handleSignOut() : handleDropDownEvent(detail);
      },
    };

    setUtilities(authStatus === "authenticated" ? [userProfile] : undefined);
  }, [user, authStatus, username]);

  /**
   * Handles user sign-out process
   * Signs out the user and redirects to home page
   *
   * @async
   */
  async function handleSignOut(): Promise<void> {
    console.log("sign out");
    signOut();
    router.push("/");
  }

  /**
   * Handles clicks on dropdown menu items
   * Currently supports navigation to user profile
   *
   * @async
   * @param {ButtonDropdownProps.ItemClickDetails} e - Details of the clicked dropdown item
   */
  async function handleDropDownEvent(
    e: ButtonDropdownProps.ItemClickDetails
  ): Promise<void> {
    if (e.id === "profile") {
      router.push("/profile");
    }
  }

  return (
    <TopNavigation
      identity={{
        logo: {
          src: "/dr-logo-valhalla-light.png",
          alt: "DeepRacer",
        },
        title: "DeepRacer Chatbot",
        href: "/",
        onFollow: followLink,
      }}
      utilities={utilities}
      i18nStrings={{
        overflowMenuTriggerText: "More",
        overflowMenuTitleText: "All",
      }}
    />
  );
}
