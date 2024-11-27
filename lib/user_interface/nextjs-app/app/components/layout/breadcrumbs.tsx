"use client";

import BreadcrumbGroup, {
  BreadcrumbGroupProps,
} from "@cloudscape-design/components/breadcrumb-group";
import { usePathname, useRouter } from "next/navigation";

interface BreadcrumbItem {
  text: string;
  href: string;
}

export interface BreadcrumbsProps {
  active: BreadcrumbGroupProps.Item;
}

const formatPathSegment = (segment: string): string => {
  if (!segment) return "";
  return segment.charAt(1).toUpperCase() + segment.slice(2);
};

const createBreadCrumbsFromPathname = (pathname: string): BreadcrumbItem[] => {
  // Handle empty or root pathname
  if (!pathname || pathname === "/") {
    return [{ text: "Home", href: "/" }];
  }

  const items: BreadcrumbItem[] = [{ text: "Home", href: "/" }];
  const segments = pathname
    .slice(1) // Remove leading slash
    .split("/") // Split into segments
    .map((segment) => `/${segment}`); // Add slash back to each segment

  return segments.reduce(
    (acc: BreadcrumbItem[], segment: string, index: number) => {
      const urlPath = segments.slice(0, index + 1).join("");
      acc.push({
        text: formatPathSegment(segment),
        href: urlPath,
      });
      return acc;
    },
    items
  );
};

export default function Breadcrumbs(): JSX.Element {
  const router = useRouter();
  const pathname = usePathname();

  const handleNavigation = (e: CustomEvent): void => {
    e.preventDefault();
    router.push(e.detail.href);
  };

  const breadcrumbItems = createBreadCrumbsFromPathname(pathname);

  return (
    <BreadcrumbGroup items={breadcrumbItems} onFollow={handleNavigation} />
  );
}
