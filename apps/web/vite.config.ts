import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";

const fileMock = fileURLToPath(new URL("./src/__mocks__/fileMock.ts", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      // absolute /vite.svg (default template uses this)
      { find: /^\/vite\.svg$/, replacement: fileMock },
      // any image asset import in tests (don't mock CSS — needed by dev server)
      { find: /\.(svg|png|jpg|jpeg|gif|webp)$/i, replacement: fileMock },
    ],
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/setupTests.ts",
    globals: true,
  },
});
