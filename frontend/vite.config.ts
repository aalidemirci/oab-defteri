import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";

// Vite yapılandırması — aile iskeletinden uyarlandı. Sürüm gömme (`define`) ve
// vendor chunk bölme yoktur: masaüstü programında gerek yok. Build çıktısı
// standart `dist/` bırakılır; Django onu SPA olarak sunar, masaüstü paketi bu
// dizini taşır (tasarım §4.1; `packaging/pyinstaller/oab_defteri.spec`).
export default defineConfig({
  plugins: [react()],
  resolve: {
    // `@/lib/api` → `src/lib/api`. tsconfig.json `paths` ile birebir eşleşmeli.
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0", // container dışından erişilebilsin
    port: 5173,
    strictPort: true,
    // Geliştirmede backend Docker Compose ağında `backend` servis adıyla erişilir.
    // Container DIŞINDA (host'tan doğrudan `vite dev` yapılmaz — aile kuralı; test
    // ve lint yalnız Docker'da: CLAUDE.md §2 madde 7; yalnız referans için)
    // `http://127.0.0.1:8000` olurdu.
    proxy: {
      "/api": { target: "http://backend:8000", changeOrigin: true },
    },
    // Windows bind-mount'ta dosya olayları güvenilmez — HMR için polling şart.
    watch: { usePolling: true },
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
  },
});
