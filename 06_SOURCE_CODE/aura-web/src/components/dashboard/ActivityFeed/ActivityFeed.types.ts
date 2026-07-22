import type { ActivityCardProps } from "../ActivityCard.types";

export interface ActivityFeedProps {
  title?: string;
  activities: ActivityCardProps[];
  onViewAll?: () => void;
}