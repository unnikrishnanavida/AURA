import type { ReactNode } from "react";
import { createContext, useContext, useState } from "react";

interface User {

    id: string;
    name: string;

}

interface AuthContextType {

    user: User | null;

    login: (
        user: User,
    ) => void;

    logout: () => void;

}

const AuthContext =
createContext<AuthContextType | null>(
    null,
);

interface AuthProviderProps {

    children: ReactNode;

}

const AuthProvider = ({
    children,
}: AuthProviderProps) => {

    const [user, setUser] =
    useState<User | null>(null);

    const login = (
        currentUser: User,
    ) => {

        setUser(currentUser);

    };

    const logout = () => {

        setUser(null);

    };

    return (

        <AuthContext.Provider
            value={{
                user,
                login,
                logout,
            }}
        >

            {children}

        </AuthContext.Provider>

    );

};

export const useAuth = () => {

    const context =
    useContext(AuthContext);

    if (!context) {

        throw new Error(
            "useAuth must be used inside AuthProvider",
        );

    }

    return context;

};

export default AuthProvider;