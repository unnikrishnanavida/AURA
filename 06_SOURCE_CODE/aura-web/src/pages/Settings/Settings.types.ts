export type ThemeMode =
    | "Light"
    | "Dark"
    | "System";

export type NotificationLevel =
    | "All"
    | "Important"
    | "Critical"
    | "None";

export interface UserSettings {

    fullName: string;

    email: string;

    organization: string;

    defaultModel: string;

    theme: ThemeMode;

    language: string;

    timezone: string;

    notifications: NotificationLevel;

    autoSave: boolean;

    analytics: boolean;

    twoFactorAuth: boolean;

}

export interface ApiKey {

    id: string;

    name: string;

    createdAt: string;

    lastUsed: string;

    status: "Active" | "Revoked";

}

export interface SettingsProps {

    className?: string;

}