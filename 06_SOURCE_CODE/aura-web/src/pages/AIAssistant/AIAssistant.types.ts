export type AssistantModel =
    | "GPT-5"
    | "Claude Sonnet 4"
    | "Gemini 2.5 Pro"
    | "Llama 3.3 70B"
    | "Mistral Large"
    | "DeepSeek R1";

export type MessageRole =
    | "user"
    | "assistant"
    | "system";

export interface ChatMessage {

    id: string;

    role: MessageRole;

    content: string;

    timestamp: string;

    tokens?: number;

}

export interface Conversation {

    id: string;

    title: string;

    lastUpdated: string;

}

export interface PromptSuggestion {

    id: string;

    title: string;

    prompt: string;

}

export interface AIAssistantProps {

    className?: string;

}