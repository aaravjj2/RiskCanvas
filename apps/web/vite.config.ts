import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const proxyConfig = {
  "/api": {
    target: "http://localhost:8090",
    changeOrigin: true,
    rewrite: (p: string) => p.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      // @ path alias for components
      { find: "@", replacement: path.resolve(__dirname, "./src") },
    ],
  },
  server: { proxy: proxyConfig },
  preview: { proxy: proxyConfig },
});
