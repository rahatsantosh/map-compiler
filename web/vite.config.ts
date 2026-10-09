import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/wms": "http://127.0.0.1:8000",
      "/std": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
    },
  },
});
