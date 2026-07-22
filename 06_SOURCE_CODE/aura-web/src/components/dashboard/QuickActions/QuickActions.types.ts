import type { LucideIcon } from "lucide-react";

export interface QuickAction {
  id: string;
  title: string;
  subtitle?: string;
  icon: LucideIcon;
  onClick: () => void;
}

export interface QuickActionsProps {
  actions: QuickAction[];
}