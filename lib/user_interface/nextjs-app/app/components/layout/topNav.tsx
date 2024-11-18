"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import {
  ButtonDropdownProps,
  TopNavigation,
  TopNavigationProps,
} from "@cloudscape-design/components";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function TopNav() {
  const router = useRouter();
  // hook below is only reevaluated when `user` changes
  const { authStatus, user, signOut } = useAuthenticator((context) => [
    context.user,
  ]);
  useAuthenticator((context) => [context.user]);
  const [utilities, setUtilities] = useState<TopNavigationProps.Utility[]>();

  function followLink(e: CustomEvent) {
    e.preventDefault();
    router.push(e.detail.href);
  }

  let username;
  if (user !== undefined) {
    username = user.signInDetails!.loginId!;
  } else {
    username = "";
  }

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
        if (detail.id === "signout") {
          handleSignOut();
        } else {
          handleDropDownEvent(detail);
        }
      },
    };

    if (authStatus === "authenticated") {
      setUtilities([userProfile]);
    } else {
      setUtilities(undefined);
    }
    return () => {
      // Unmounting
    };
  }, [user]);

  async function handleSignOut() {
    console.log("sign out");
    signOut();
    router.push("/");
  }

  async function handleDropDownEvent(e: ButtonDropdownProps.ItemClickDetails) {
    console.log(e);
    if (e.id === "profile") {
      router.push("/profile");
    }
  }

  return (
    <TopNavigation
      identity={{
        logo: { src: "/dr-logo-valhalla-light.png", alt: "DeepRacer" },
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
