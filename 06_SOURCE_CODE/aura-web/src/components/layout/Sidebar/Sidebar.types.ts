import type { LucideIcon } from "lucide-react";

export interface SidebarItem {
  title: string;
  icon: LucideIcon;
  path: string;
}

export interface SidebarProps {
  collapsed?: boolean;
}