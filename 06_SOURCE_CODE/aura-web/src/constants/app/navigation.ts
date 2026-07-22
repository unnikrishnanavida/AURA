import {
    LayoutDashboard,
    Bot,
    MessageSquare,
    Brain,
    Database,
    FolderOpen,
    BarChart3,
    Settings,
    Shield,
    User,
} from "lucide-react";

export const navigation = [
    {
        title: "Dashboard",
        path: "/dashboard",
        icon: LayoutDashboard,
    },
    {
        title: "Agents",
        path: "/agents",
        icon: Bot,
    },
    {
        title: "Chat",
        path: "/chat",
        icon: MessageSquare,
    },
    {
        title: "Brain",
        path: "/brain",
        icon: Brain,
    },
    {
        title: "Knowledge",
        path: "/knowledge",
        icon: Database,
    },
    {
        title: "Files",
        path: "/files",
        icon: FolderOpen,
    },
    {
        title: "Analytics",
        path: "/analytics",
        icon: BarChart3,
    },
    {
        title: "Security",
        path: "/security",
        icon: Shield,
    },
    {
        title: "Profile",
        path: "/profile",
        icon: User,
    },
    {
        title: "Settings",
        path: "/settings",
        icon: Settings,
    },
];