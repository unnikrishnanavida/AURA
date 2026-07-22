export interface UserProfile {

    id: string;

    fullName: string;

    email: string;

    role: string;

    organization: string;

    department: string;

    location: string;

    bio: string;

    joinedDate: string;

    avatar: string;

}

export interface Achievement {

    id: string;

    title: string;

    description: string;

    earnedOn: string;

}

export interface ConnectedAccount {

    id: string;

    provider: string;

    username: string;

    status: "Connected" | "Disconnected";

}

export interface Activity {

    id: string;

    title: string;

    description: string;

    timestamp: string;

}

export interface ProfileStatistics {

    projects: number;

    workflows: number;

    conversations: number;

    apiRequests: number;

}

export interface ProfileProps {

    className?: string;

}