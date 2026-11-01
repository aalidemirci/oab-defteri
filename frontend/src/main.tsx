// main.tsx — aile iskeletinden uyarlandı. Web uygulamalarındaki AuthProvider,
// Sentry ve Google OAuth katmanları yoktur: program yerel sunucuyla çalışan
// çevrimdışı bir masaüstü programıdır, telemetri göndermez (tasarım §4.1, TK4).
// QueryClient/Snackbar/Confirm sağlayıcıları ve tema ilklemesi (FOUC önleme)
// korunur.

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { initDensityFromStorage } from "./hooks/useDensity";
import { initThemeFromStorage } from "./hooks/useTheme";
import { queryClient } from "./lib/queryClient";
import { ConfirmProvider } from "./ui/ConfirmProvider";
import { SnackbarProvider } from "./ui/SnackbarProvider";
import "./index.css";

// Tema'yı React mount'undan ÖNCE uygula — FOUC olmadan açık/karanlık. Kullanıcı
// tercihi localStorage'da yoksa sistem `prefers-color-scheme` esas alınır.
initThemeFromStorage();
initDensityFromStorage();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SnackbarProvider>
          <ConfirmProvider>
            <App />
          </ConfirmProvider>
        </SnackbarProvider>
      </BrowserRouter>
      {import.meta.env.DEV && (
        <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
      )}
    </QueryClientProvider>
  </StrictMode>,
);
