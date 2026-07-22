export interface LandingProps {
    className?: string;
}

export interface FeatureCard {
    id: string;
    title: string;
    description: string;
    icon: string;
}

export interface Statistic {
    label: string;
    value: string;
}

export interface Testimonial {
    id: string;
    name: string;
    role: string;
    company: string;
    quote: string;
}