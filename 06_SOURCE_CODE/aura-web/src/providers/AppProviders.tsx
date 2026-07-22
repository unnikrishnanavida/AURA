import type { ReactNode } from "react";

import { Provider }
from "react-redux";

import { store }
from "../store/store";

import AuthProvider
from "./auth/AuthProvider";

import QueryProvider
from "./query/QueryProvider";

import ThemeProvider
from "./theme/ThemeProvider";

interface Props {

    children: ReactNode;

}

const AppProviders = ({
    children,
}: Props) => {

    return (

        <Provider store={store}>

            <ThemeProvider>

                <QueryProvider>

                    <AuthProvider>

                        {children}

                    </AuthProvider>

                </QueryProvider>

            </ThemeProvider>

        </Provider>

    );

};

export default AppProviders;