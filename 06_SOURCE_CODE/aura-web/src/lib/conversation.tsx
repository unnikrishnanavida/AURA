/**
 * Conversation — the AURA chat surface.
 *
 * A user-centred AI conversation: welcome hero on first open, then a clean
 * thread of user questions and structured AURA answers. Only high-level
 * activity states are shown ("AURA is thinking…") — never chain-of-thought.
 * Answers come live from the real reasoning API; nothing is fabricated.
 */

import { useEffect, useRef, useState } from "react";
import { Plus } from "lucide-react";

import { ChatComposer } from "../components/chat/ChatComposer";
import { FormattedAnswer } from "../components/chat/FormattedAnswer";
import { SuggestedPrompts, type SuggestedPrompt } from "../components/chat/SuggestedPrompts";
import { AuraLogo } from "../components/aura/AuraLogo";
import { ApiError } from "./api";
import { useSettings } from "./settings-context";
import type { ProviderStatus, ReasonResult, ReasoningContext } from "./types";

export interface Turn {
  question: string;
  answer?: string;
  confidence?: number | null;
  uncertainty?: string | null;
  provider?: string | null;
  providerMode?: string | null;
  providerStatus?: ProviderStatus | null;
  providerModel?: string | null;
  providerVerified?: boolean;
  abstentionReason?: string;
  grounded?: boolean;
  context?: ReasoningContext;
  status: "ok" | "error" | "cancelled";
  message?: string;
}

interface ConversationProps {
  onNavigate?: (tab: string) => void;
  onTitleChange?: (title: string) => void;
}

function friendlyMessage(err: unknown): { friendly: string; detail: string } {
  if (err instanceof ApiError) {
    if (err.code === "sdk.cancelled") return { friendly: "Stopped.", detail: "" };
    if (err.code === "sdk.timeout")
      return { friendly: "AURA took too long to respond. Please try again.", detail: err.message };
    if (err.code === "api.auth_failed")
      return { friendly: "Your connection expired. Sign in again to continue.", detail: err.message };
    if (err.code === "api.forbidden" || err.status === 403)
      return {
        friendly: "This connection isn't allowed to do that. Its access key may need different permissions.",
        detail: err.message,
      };
    if (err.status === 0)
      return { friendly: "AURA couldn't reach the connection. Check that AURA is running, then try again.", detail: err.message };
    if (err.status >= 400 && err.status < 500)
      return { friendly: "I couldn't process that request. Please check the information and try again.", detail: err.message };
    return { friendly: "AURA hit an unexpected issue. Please try again.", detail: err.message };
  }
  return { friendly: "AURA couldn't reach the connection. Check that AURA is running, then try again.", detail: err instanceof Error ? err.message : String(err) };
}

function hasContext(context?: ReasoningContext): boolean {
  return (context?.items.length ?? 0) > 0;
}

/**
 * Turns a provider outcome into something a person can act on.
 *
 * Each state gets its own sentence because "something went wrong" hides the
 * difference between AURA having no model configured (expected, local-first)
 * and AURA having one that is down or refusing (an operator problem).
 */
function providerNotice(status?: ProviderStatus | null): string | null {
  switch (status) {
    case "not_configured":
      return "AURA can reason over your saved information, but no language model is currently configured for broader generation.";
    case "unauthorized":
      return "This connection isn't allowed to use AURA's language model. Its access key needs different permissions.";
    case "timeout":
      return "AURA's language model took too long to respond. Please try again.";
    case "rate_limited":
      return "AURA's language model is busy right now. Please try again in a moment.";
    case "authentication_failed":
      return "AURA's language model rejected its configured credentials. An administrator needs to check the provider setup.";
    case "forbidden":
      return "AURA's language model refused the request. An administrator needs to check the provider permissions.";
    case "unavailable":
    case "transient_failure":
      return "AURA's language model couldn't be reached. AURA answered using your saved information instead.";
    case "model_unavailable":
      return "The language model AURA is configured to use isn't available right now.";
    case "malformed_response":
      return "AURA's language model returned an unexpected response. AURA fell back to your saved information.";
    case "budget_exceeded":
      return "This request exceeded the configured limits for AURA's language model.";
    default:
      return null;
  }
}

const SOURCE_LABEL: Record<string, string> = {
  memory: "Saved memory",
  knowledge: "Stored knowledge",
};

/**
 * Shows exactly what AURA retrieved behind an answer — the record it came
 * from, whether that record is verified knowledge or an unverified saved note,
 * and any contradiction it refused to resolve. Nothing here is inferred: every
 * row is a real item from the request's context.
 */
function ContextAttribution({ context }: { context: ReasoningContext | undefined }) {
  if (!context || context.items.length === 0) return null;
  return (
    <>
      {context.items.map((item) => (
        <div className="turn-context" key={`${item.source}-${item.reference}`}>
          <dt className="turn-meta-dt">{SOURCE_LABEL[item.source] ?? item.source}</dt>
          <dd className="turn-meta-dd">
            <span className="turn-context-text">{item.text}</span>
            <span className="turn-context-tags">
              {item.source === "knowledge" ? (item.verified ? "verified" : "unverified") : "saved by you"}
              {item.contradicted ? " · conflicting" : ""}
            </span>
          </dd>
        </div>
      ))}
      {context.contradictions.length > 0 ? (
        <>
          <dt className="turn-meta-dt">Conflicts</dt>
          <dd className="turn-meta-dd">
            {context.contradictions.length} conflicting record
            {context.contradictions.length === 1 ? "" : "s"} found — AURA did not pick a side.
          </dd>
        </>
      ) : null}
      {context.dropped > 0 ? (
        <>
          <dt className="turn-meta-dt">Not included</dt>
          <dd className="turn-meta-dd">
            {context.dropped} lower-ranked record{context.dropped === 1 ? "" : "s"} left out to keep
            the answer focused.
          </dd>
        </>
      ) : null}
    </>
  );
}

export function Conversation({ onNavigate, onTitleChange }: ConversationProps) {
  const { api } = useSettings();
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [controller, setController] = useState<AbortController | null>(null);
  const threadRef = useRef<HTMLDivElement | null>(null);
  const conversationGeneration = useRef(0);

  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, busy]);

  function run(turnIndex: number, text: string) {
    if (controller) controller.abort();
    const current = new AbortController();
    const generation = conversationGeneration.current;
    const history = turns
      .slice(0, turnIndex)
      .filter((turn) => turn.answer !== undefined)
      .flatMap((turn) => [
        { role: "user" as const, content: turn.question },
        { role: "assistant" as const, content: turn.answer ?? "" },
      ])
      .slice(-20);
    setController(current);
    setBusy(true);
    setTurns((previous) => {
      const next = [...previous];
      next[turnIndex] = { question: text, status: "ok" };
      return next;
    });
    void api
      .reason(text, {}, current.signal, history)
      .then((result: ReasonResult) => {
        if (generation !== conversationGeneration.current) return;
        setTurns((previous) => {
          const next = [...previous];
          next[turnIndex] = {
            question: text,
            answer: result.answer ?? "(no answer)",
            confidence: result.confidence,
            uncertainty: result.uncertainty,
            provider: result.provider?.name,
            providerMode: result.provider?.mode,
            providerStatus: result.provider?.status,
            providerModel: result.provider?.model,
            providerVerified: result.provider?.verified,
            abstentionReason: result.abstention_reason,
            grounded: result.grounded,
            context: result.context,
            status: "ok",
          };
          return next;
        });
      })
      .catch((err: unknown) => {
        if (generation !== conversationGeneration.current) return;
        const cancelled = err instanceof ApiError && err.code === "sdk.cancelled";
        setTurns((previous) => {
          const next = [...previous];
          next[turnIndex] = {
            question: text,
            status: cancelled ? "cancelled" : "error",
            message: cancelled ? "Stopped." : friendlyMessage(err).friendly,
          };
          return next;
        });
      })
      .finally(() => {
        if (generation === conversationGeneration.current) {
          setBusy(false);
          setController(null);
        }
      });
  }

  function startNewChat() {
    conversationGeneration.current += 1;
    controller?.abort();
    setController(null);
    setBusy(false);
    setQuestion("");
    setTurns([]);
    onTitleChange?.("New chat");
  }

  async function onSubmit() {
    const text = question.trim();
    if (!text || busy) return;
    setQuestion("");
    onTitleChange?.(text.length > 48 ? `${text.slice(0, 47)}…` : text);
    const turnIndex = turns.length;
    setTurns([...turns, { question: text, status: "ok" }]);
    run(turnIndex, text);
  }

  function retry(turnIndex: number) {
    const questionText = turns[turnIndex]?.question ?? "";
    if (questionText && !busy) run(turnIndex, questionText);
  }

  function cancel() {
    if (controller) controller.abort();
  }

  function pickPrompt(prompt: SuggestedPrompt) {
    if (prompt.target === "navigate" && prompt.navigateTo) {
      onNavigate?.(prompt.navigateTo);
      return;
    }
    const next = prompt.prompts[0] ?? "";
    setQuestion(next);
  }

  const hasConversation = turns.length > 0 || busy;

  return (
    <section aria-label="Chat with AURA" className={hasConversation ? "chat-surface has-thread" : "chat-surface"}>
      {hasConversation ? (
        <>
          <div className="chat-topline">
            <AuraLogo variant="horizontal" className="chat-topline-logo" />
            <button
              type="button"
              className="ghost chat-new"
              onClick={startNewChat}
            >
              <Plus aria-hidden="true" /> New chat
            </button>
          </div>
          <div
            className="chat-thread"
            ref={threadRef}
            role="log"
            aria-label="Conversation with AURA"
            aria-live="polite"
            aria-busy={busy}
          >
            <div className="thread-inner">
              {turns.map((turn, index) => (
                <article
                  key={`${index}-${turn.question}`}
                  className={
                    turn.status === "ok"
                      ? "turn turn-aura"
                      : turn.status === "cancelled"
                        ? "turn turn-aura turn-cancelled"
                        : "turn turn-aura turn-error"
                  }
                >
                  <div className="bubble user">
                    <p className="turn-question">{turn.question}</p>
                  </div>
                  <div className="bubble aura">
                    {turn.status === "ok" && turn.answer ? (
                      <div className="turn-answer">
                        <FormattedAnswer text={turn.answer} />
                        {turn.confidence !== undefined || turn.uncertainty || turn.provider || hasContext(turn.context) ? (
                          <details className="turn-response-details">
                            <summary>
                              {hasContext(turn.context)
                                ? `Answer details — based on ${turn.context?.items.length} saved ${
                                    turn.context?.items.length === 1 ? "item" : "items"
                                  }`
                                : "Response details"}
                            </summary>
                            <dl className="turn-metadata">
                              {hasContext(turn.context) ? (
                                <ContextAttribution context={turn.context} />
                              ) : null}
                              {turn.providerMode !== "generation" && turn.confidence !== undefined && turn.confidence !== null ? (
                                <>
                                  <dt className="turn-meta-dt">Confidence</dt>
                                  <dd className="turn-meta-dd">{turn.confidence.toFixed(2)}</dd>
                                </>
                              ) : null}
                              {turn.providerMode !== "generation" && turn.uncertainty ? (
                                <>
                                  <dt className="turn-meta-dt">Uncertainty</dt>
                                  <dd className="turn-meta-dd">{turn.uncertainty}</dd>
                                </>
                              ) : null}
                              {turn.provider ? (
                                <>
                                  <dt className="turn-meta-dt">
                                    {turn.providerMode === "generation" ? "Answered by" : "Synthesized by"}
                                  </dt>
                                  <dd className="turn-meta-dd">
                                    {turn.provider}
                                    {turn.providerModel ? ` (${turn.providerModel})` : ""}
                                    {turn.providerVerified === false ? " · not independently verified" : ""}
                                  </dd>
                                </>
                              ) : null}
                            </dl>
                          </details>
                        ) : null}
                      </div>
                    ) : null}
                    {providerNotice(turn.providerStatus) ? (
                          <p className="hint turn-provider-notice">
                            {providerNotice(turn.providerStatus)}
                          </p>
                        ) : null}
                        {turn.status === "cancelled" ? <p className="hint">Stopped.</p> : null}
                    {turn.status === "error" ? (
                      <div role="alert">
                        <p className="error">{turn.message ?? "Something went wrong."}</p>
                        <button type="button" className="ghost" onClick={() => retry(index)} disabled={busy}>
                          Retry
                        </button>
                      </div>
                    ) : null}
                  </div>
                </article>
              ))}
              {busy ? (
                <article className="turn turn-aura turn-thinking" aria-live="polite">
                  <div className="thinking">
                    <span className="thinking-dots" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </span>
                    <span className="thinking-label">AURA is thinking…</span>
                  </div>
                </article>
              ) : null}
            </div>
          </div>
        </>
      ) : null}

      {!hasConversation ? (
        <div className="chat-welcome">
          <div className="welcome-inner">
            <AuraLogo variant="stacked" className="welcome-logo" />
            <h1>How can I help you today?</h1>
            <p className="welcome-sub">Ask, explore, research, create, and understand.</p>
            <ChatComposer
              id="chat-input"
              value={question}
              onChange={setQuestion}
              onSubmit={() => void onSubmit()}
              busy={busy}
              onStop={cancel}
            />
            <SuggestedPrompts onPick={pickPrompt} />
          </div>
        </div>
      ) : (
        <div className="chat-dock">
          <div className="dock-inner">
            <ChatComposer
              id="chat-input"
              value={question}
              onChange={setQuestion}
              onSubmit={() => void onSubmit()}
              busy={busy}
              onStop={cancel}
            />
          </div>
        </div>
      )}
    </section>
  );
}

export { FormattedAnswer };
export { ChatComposer };