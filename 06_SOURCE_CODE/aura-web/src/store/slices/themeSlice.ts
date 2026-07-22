import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

type ThemeMode =
"dark" | "light";

interface ThemeState {

    mode: ThemeMode;

}

const initialState: ThemeState = {

    mode: "dark",

};

const themeSlice = createSlice({

    name: "theme",

    initialState,

    reducers: {

        setTheme: (
            state,
            action:
            PayloadAction<ThemeMode>,
        ) => {

            state.mode =
            action.payload;

        },

    },

});

export const {

    setTheme,

} = themeSlice.actions;

export default themeSlice.reducer;