'use client'

import BreadcrumbGroup, { BreadcrumbGroupProps } from '@cloudscape-design/components/breadcrumb-group';
import { usePathname, useRouter } from 'next/navigation';

export interface BreadcrumbsProps {
  active: BreadcrumbGroupProps.Item;
}

function createBreadCrumbsFromPathname(pathname: string) {
  const items = [];
  const slicedPathname = pathname.slice(1);
  let segments = slicedPathname.split("/");
  segments = segments.map((i) => "/" + i);
  items.push({ text: "Home", href: "/" });
  let urlStem = "";
  segments.forEach((i) => {
    urlStem = urlStem + i;
    // Capitol first letter
    let text = i.charAt(1).toUpperCase() + i.slice(2);
    // let text = i.slice(1);
    items.push({
      text: text,
      href: urlStem,
    });
  });
  return items;
}

export default function Breadcrumbs() {
  const router = useRouter()

  function followLink(e: CustomEvent) {
    e.preventDefault();
    router.push(e.detail.href);
  }

  const items = createBreadCrumbsFromPathname(usePathname());
  return <BreadcrumbGroup items={items} onFollow={followLink}/>;
}
