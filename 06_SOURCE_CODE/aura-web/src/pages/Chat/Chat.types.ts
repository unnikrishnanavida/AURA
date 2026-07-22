export type MessageRole =
    | "user"
    | "assistant"
    | "system";

export type MessageStatus =
    | "sending"
    | "sent"
    | "streaming"
    | "error";

export interface ChatAttachment {
    id: string;
    name: string;
    type: string;
    size: string;
}

export interface ChatMessage {
    id: string;

    role: MessageRole;

    content: string;

    timestamp: string;

    status: MessageStatus;

    model: string;

    tokens: number;

    attachments?: ChatAttachment[];
}

export interface Conversation {

    id: string;

    title: string;

    updatedAt: string;

    pinned: boolean;

    unread: boolean;

}

export interface ChatProps {

    className?: string;

}