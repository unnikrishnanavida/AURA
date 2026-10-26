/**
 * Home — the AURA conversational home. The first thing a user sees is the
 * AURA identity, a greeting, a large chat composer and a few suggested
 * prompts. Once the user talks to AURA the page becomes the conversation —
 * the composer stays anchored at the bottom.
 */

import { Conversation } from "../lib/conversation";

interface HomePageProps {
  onNavigate: (tab: string) => void;
}

export function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div className="page chat-page" aria-label="Home">
      <Conversation onNavigate={onNavigate} />
    </div>
  );
}