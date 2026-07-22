export interface AdminProps {
    className?: string;
}

export interface AdminUser {
    id: string;
    name: string;
    email: string;
    role: string;
    status: "Active" | "Inactive" | "Pending";
}

export interface SystemMetric {
    label: string;
    value: string;
    change: string;
}

export interface AuditLog {
    id: string;
    user: string;
    action: string;
    timestamp: string;
}

export interface InfrastructureService {
    id: string;
    name: string;
    status: "Healthy" | "Warning" | "Critical";
    uptime: string;
}