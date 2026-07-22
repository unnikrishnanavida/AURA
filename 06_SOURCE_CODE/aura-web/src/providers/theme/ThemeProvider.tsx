import type { ReactNode } from "react";

interface ThemeProviderProps {
    children: ReactNode;
}

const ThemeProvider = ({
    children,
}: ThemeProviderProps) => {

    return (
        <>
            {children}
        </>
    );

};

export default ThemeProvider;