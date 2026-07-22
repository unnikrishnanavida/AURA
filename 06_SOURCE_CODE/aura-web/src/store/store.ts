import {
    configureStore,
} from "@reduxjs/toolkit";

import { useDispatch, useSelector } from "react-redux";
import type { TypedUseSelectorHook } from "react-redux";

import authReducer from "./slices/authSlice";
import themeReducer from "./slices/themeSlice";
import userReducer from "./slices/userSlice";

export const store = configureStore({

    reducer: {

        auth: authReducer,
        theme: themeReducer,
        user: userReducer,

    },

});

export type RootState =
ReturnType<typeof store.getState>;

export type AppDispatch =
typeof store.dispatch;

export const useAppDispatch =
() => useDispatch<AppDispatch>();

export const useAppSelector:
TypedUseSelectorHook<RootState> =
useSelector;