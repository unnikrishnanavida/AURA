export type ResearchStatus =
  | "processing"
  | "completed"
  | "failed";

export interface ResearchCardProps {
  title: string;
  source: string;
  description: string;
  confidence: number;
  status: ResearchStatus;
  updatedAt: string;
  onOpen?: () => void;
}