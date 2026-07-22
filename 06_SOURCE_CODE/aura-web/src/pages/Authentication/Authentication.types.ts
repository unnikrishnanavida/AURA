export interface AuthenticationProps {
    className?: string;
}

export interface AuthProvider {
    id: string;
    name: string;
    icon: string;
}

export interface AuthAction {
    title: string;
    description: string;
    route: string;
}