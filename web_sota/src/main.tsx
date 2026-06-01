import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { BookmarkSettingsProvider } from "@/common/bookmark-settings";
import { ToastProvider } from "@/components/ui/toast";

const root = document.getElementById("root");
if (root) {
  ReactDOM.createRoot(root).render(
    <React.StrictMode>
      <ToastProvider>
        <BookmarkSettingsProvider>
          <App />
        </BookmarkSettingsProvider>
      </ToastProvider>
    </React.StrictMode>,
  );
}
