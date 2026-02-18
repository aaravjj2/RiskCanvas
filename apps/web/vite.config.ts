import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      // @ path alias for components
      { find: "@", replacement: path.resolve(__dirname, "./src") },
    ],
  },
});
