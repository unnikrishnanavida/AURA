import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { SettingsProvider } from "./lib/settings";
import "./styles/index.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <SettingsProvider>
      <App />
    </SettingsProvider>
  </StrictMode>,
);