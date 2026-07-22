import { useState } from "react";
import {
    Mic,
    Paperclip,
    Plus,
    Send,
} from "lucide-react";

import styles from "./AIAssistant.module.css";

import type {
    AssistantModel,
    ChatMessage,
    Conversation,
    PromptSuggestion,
} from "./AIAssistant.types";

const conversations: Conversation[] = [
    {
        id: "1",
        title: "Enterprise Architecture",
        lastUpdated: "5 mins ago",
    },
    {
        id: "2",
        title: "Cloud Deployment",
        lastUpdated: "Yesterday",
    },
    {
        id: "3",
        title: "AI Research",
        lastUpdated: "2 days ago",
    },
];

const suggestions: PromptSuggestion[] = [
    {
        id: "1",
        title: "Generate Report",
        prompt: "Create an executive project report.",
    },
    {
        id: "2",
        title: "Analyze Data",
        prompt: "Analyze system performance trends.",
    },
    {
        id: "3",
        title: "Write Code",
        prompt: "Generate a production-ready React component.",
    },
];

const initialMessages: ChatMessage[] = [
    {
        id: "1",
        role: "assistant",
        content:
            "Welcome to AURA AI Assistant. How can I help you today?",
        timestamp: "09:00",
        tokens: 24,
    },
];

const AIAssistant = () => {

    const [model, setModel] =
        useState<AssistantModel>("GPT-5");

    const [messages, setMessages] =
        useState<ChatMessage[]>(initialMessages);

    const [input, setInput] =
        useState("");

    return (

        <main className={styles.page}>

            {/* ================= SIDEBAR ================= */}

            <aside className={styles.sidebar}>

                <h2 className={styles.sidebarTitle}>
                    Conversations
                </h2>

                <button className={styles.newChat}>

                    <Plus size={18} />

                    New Chat

                </button>

                <div className={styles.conversationList}>

                    {conversations.map((conversation) => (

                        <div
                            key={conversation.id}
                            className={styles.conversation}
                        >

                            <div
                                className={styles.conversationTitle}
                            >
                                {conversation.title}
                            </div>

                            <div
                                className={styles.conversationTime}
                            >
                                {conversation.lastUpdated}
                            </div>

                        </div>

                    ))}

                </div>

            </aside>

            {/* ================= CHAT ================= */}

            <section className={styles.chatArea}>

                {/* ---------- Header ---------- */}

                <header className={styles.header}>

                    <h1 className={styles.title}>
                        AI Assistant
                    </h1>

                    <select
                        className={styles.modelSelect}
                        value={model}
                        onChange={(e) =>
                            setModel(
                                e.target.value as AssistantModel
                            )
                        }
                    >

                        <option>GPT-5</option>
                        <option>Claude Sonnet 4</option>
                        <option>Gemini 2.5 Pro</option>
                        <option>Llama 3.3 70B</option>
                        <option>Mistral Large</option>
                        <option>DeepSeek R1</option>

                    </select>

                </header>

                {/* ---------- Prompt Suggestions ---------- */}

                <div
                    style={{
                        display: "flex",
                        gap: 12,
                        padding: "16px 24px",
                        overflowX: "auto",
                    }}
                >

                    {suggestions.map((suggestion) => (

                        <button
                            key={suggestion.id}
                            className={styles.iconButton}
                            style={{
                                width: "auto",
                                padding: "12px 18px",
                            }}
                            onClick={() =>
                                setInput(suggestion.prompt)
                            }
                        >
                            {suggestion.title}
                        </button>

                    ))}

                </div>

                {/* ---------- Messages ---------- */}

                <div className={styles.messages}>

                    {messages.map((message) => (

                        <article
                            key={message.id}
                            className={`${styles.message} ${
                                message.role === "user"
                                    ? styles.user
                                    : styles.assistant
                            }`}
                        >

                            <div className={styles.role}>
                                {message.role.toUpperCase()}
                            </div>

                            <div className={styles.content}>
                                {message.content}
                            </div>

                            <div className={styles.time}>
                                {message.timestamp}
                            </div>

                        </article>

                    ))}

                </div>
                                {/* ================= COMPOSER ================= */}

                <footer className={styles.composer}>

                    <button
                        className={styles.iconButton}
                        title="Attach File"
                    >
                        <Paperclip size={20} />
                    </button>

                    <button
                        className={styles.iconButton}
                        title="Voice Input"
                    >
                        <Mic size={20} />
                    </button>

                    <input
                        className={styles.input}
                        placeholder="Ask AURA anything..."
                        value={input}
                        onChange={(e) =>
                            setInput(e.target.value)
                        }
                        onKeyDown={(e) => {

                            if (
                                e.key === "Enter" &&
                                input.trim()
                            ) {

                                setMessages((previous) => [

                                    ...previous,

                                    {
                                        id: Date.now().toString(),
                                        role: "user",
                                        content: input,
                                        timestamp: new Date().toLocaleTimeString(
                                            [],
                                            {
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            }
                                        ),
                                        tokens: Math.ceil(
                                            input.length / 4
                                        ),
                                    },

                                ]);

                                setInput("");

                            }

                        }}
                    />

                    <button
                        className={styles.sendButton}
                        title="Send"
                        onClick={() => {

                            if (!input.trim()) return;

                            setMessages((previous) => [

                                ...previous,

                                {
                                    id: Date.now().toString(),
                                    role: "user",
                                    content: input,
                                    timestamp: new Date().toLocaleTimeString(
                                        [],
                                        {
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        }
                                    ),
                                    tokens: Math.ceil(
                                        input.length / 4
                                    ),
                                },

                            ]);

                            setInput("");

                        }}
                    >

                        <Send size={20} />

                    </button>

                </footer>

            </section>

        </main>

    );

};

export default AIAssistant;