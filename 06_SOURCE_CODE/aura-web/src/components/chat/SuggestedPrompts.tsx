/**
 * SuggestedPrompts — helpful starting points shown on the empty chat home.
 * Each maps to a REAL action: either pre-fills the composer or navigates to a
 * real AURA workspace. No fabricated capabilities. Prompt data lives in
 * src/lib/suggested-prompts.ts.
 */

import { BookOpen, FileText, FlaskConical, Lightbulb } from "lucide-react";
import { SUGGESTED_PROMPTS, type SuggestedPrompt } from "../../lib/suggested-prompts";

interface SuggestedPromptsProps {
  onPick: (prompt: SuggestedPrompt) => void;
}

const ICONS = [Lightbulb, FlaskConical, FileText, BookOpen];

export function SuggestedPrompts({ onPick }: SuggestedPromptsProps) {
  return (
    <div className="suggested" aria-label="Suggested prompts">
      {SUGGESTED_PROMPTS.map((prompt, i) => {
        const Icon = ICONS[i % ICONS.length];
        return (
          <button
            key={prompt.id}
            type="button"
            className="suggestion"
            onClick={() => onPick(prompt)}
          >
            <Icon aria-hidden="true" />
            <span>{prompt.label}</span>
          </button>
        );
      })}
    </div>
  );
}

export type { SuggestedPrompt };