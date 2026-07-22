export interface LoginForm {

    email: string;

    password: string;

    rememberMe: boolean;

}

export interface SocialProvider {

    id: string;

    name: string;

    icon: string;

}

export interface LoginProps {

    className?: string;

}