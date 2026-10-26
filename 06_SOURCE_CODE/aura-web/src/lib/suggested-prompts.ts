/**
 * Suggested prompt definitions — data only, kept out of the component file so
 * fast-refresh can treat SuggestedPrompts.tsx as components-only.
 */

export interface SuggestedPrompt {
  id: string;
  label: string;
  prompts: string[];
  target: "compose" | "navigate";
  navigateTo?: string;
}

export const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  { id: "explain", label: "Explain a difficult concept", prompts: ["Explain quantum computing to me like I'm a beginner."], target: "compose" },
  { id: "research", label: "Research a topic deeply", prompts: ["Research the practical risks of quantum error correction."], target: "navigate", navigateTo: "research" },
  { id: "analyze", label: "Analyze a document", prompts: [], target: "navigate", navigateTo: "documents" },
  { id: "create", label: "Help me build a project", prompts: ["Help me build a step-by-step project plan for a personal AI assistant."], target: "compose" },
];