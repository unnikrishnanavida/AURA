/**
 * Chat page — the dedicated full conversation surface (same experience as
 * the home screen once a conversation has started).
 */

import { Conversation } from "../lib/conversation";

interface ConsolePageProps {
  onNavigate?: (tab: string) => void;
  onTitleChange?: (title: string) => void;
}

export function ConsolePage({ onNavigate, onTitleChange }: ConsolePageProps = {}) {
  return (
    <div className="page chat-page" aria-label="Chat with AURA">
      <Conversation onNavigate={onNavigate} onTitleChange={onTitleChange} />
    </div>
  );
}