import { useState } from "react";
import { Plus, Send, Bot, User, Sparkles } from "lucide-react";

import styles from "./Chat.module.css";

import type {
    ChatMessage,
    Conversation,
} from "./Chat.types";

const conversations: Conversation[] = [
    {
        id: "1",
        title: "Enterprise AI Strategy",
        updatedAt: "2 min ago",
        pinned: true,
        unread: false,
    },
    {
        id: "2",
        title: "Research Assistant",
        updatedAt: "15 min ago",
        pinned: false,
        unread: true,
    },
    {
        id: "3",
        title: "Cloud Architecture",
        updatedAt: "Yesterday",
        pinned: false,
        unread: false,
    },
];

const initialMessages: ChatMessage[] = [
    {
        id: "1",
        role: "assistant",
        content:
            "Hello! Welcome to AURA Enterprise AI. How can I help you today?",
        timestamp: "10:00 AM",
        status: "sent",
        model: "GPT-5.5",
        tokens: 24,
    },
    {
        id: "2",
        role: "user",
        content:
            "Summarize the latest AI research trends in enterprise software.",
        timestamp: "10:01 AM",
        status: "sent",
        model: "",
        tokens: 18,
    },
    {
        id: "3",
        role: "assistant",
        content:
            "Recent trends include autonomous AI agents, multimodal reasoning, retrieval-augmented generation (RAG), AI copilots, and enterprise knowledge orchestration.",
        timestamp: "10:02 AM",
        status: "sent",
        model: "GPT-5.5",
        tokens: 68,
    },
];

const Chat = () => {
    const [selectedConversation] = useState("1");
    const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
    const [input, setInput] = useState("");

    const sendMessage = () => {
        if (!input.trim()) return;

        const newMessage: ChatMessage = {
            id: Date.now().toString(),
            role: "user",
            content: input,
            timestamp: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            }),
            status: "sent",
            model: "",
            tokens: input.split(" ").length,
        };

        setMessages((prev) => [...prev, newMessage]);
        setInput("");
    };

    return (
        <main className={styles.page}>
            <aside className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <h2 className={styles.sidebarTitle}>Conversations</h2>
                    <button className={styles.newChatButton}>
                        <Plus size={18} />
                        New Chat
                    </button>
                </div>

                <div className={styles.conversationList}>
                    {conversations.map((conversation) => (
                        <div
                            key={conversation.id}
                            className={`${styles.conversation} ${
                                selectedConversation === conversation.id
                                    ? styles.active
                                    : ""
                            }`}
                        >
                            <div className={styles.conversationTitle}>
                                {conversation.title}
                            </div>
                            <div className={styles.conversationTime}>
                                {conversation.updatedAt}
                            </div>
                        </div>
                    ))}
                </div>
            </aside>

            <section className={styles.chat}>
                <header className={styles.chatHeader}>
                    <div>
                        <h1 className={styles.chatTitle}>Enterprise AI Chat</h1>
                        <small>Powered by AURA Intelligence</small>
                    </div>
                    <Sparkles size={24} />
                </header>

                <div className={styles.messages}>
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`${styles.message} ${
                                styles[message.role]
                            }`}
                        >
                            <div
                                style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "10px",
                                }}
                            >
                                {message.role === "assistant" ? (
                                    <Bot size={18} />
                                ) : (
                                    <User size={18} />
                                )}
                                <strong>
                                    {message.role === "assistant"
                                        ? "AURA"
                                        : "You"}
                                </strong>
                            </div>

                            <div>{message.content}</div>

                            <div className={styles.messageFooter}>
                                <span>{message.timestamp}</span>
                                <span>{message.tokens} tokens</span>
                            </div>
                        </div>
                    ))}
                </div>

                <footer className={styles.inputArea}>
                    <div className={styles.inputWrapper}>
                        <input
                            className={styles.input}
                            type="text"
                            placeholder="Ask AURA anything..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                        />
                        <button
                            className={styles.sendButton}
                            onClick={sendMessage}
                            aria-label="Send message"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </footer>
            </section>
        </main>
    );
};

export default Chat;
