export interface RegisterForm {

    firstName: string;

    lastName: string;

    organization: string;

    email: string;

    password: string;

    confirmPassword: string;

    acceptTerms: boolean;

}

export interface SocialProvider {

    id: string;

    name: string;

    icon: string;

}

export interface RegisterProps {

    className?: string;

}