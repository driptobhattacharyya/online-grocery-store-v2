import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// In development the Flask API runs on :5000 and Vite proxies /api to it,
// so the app always talks to its own origin (same as in production).
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  build: {
    sourcemap: false,
  },
  server: {
    port: 8080,
    proxy: {
      "/api": "http://127.0.0.1:5000",
    },
  },
});
