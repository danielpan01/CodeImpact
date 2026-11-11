import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiPort = Number(process.env.CODEIMPACT_API_PORT ?? 8000);
const webPort = Number(process.env.CODEIMPACT_WEB_PORT ?? 5173);
if (
  ![apiPort, webPort].every(
    (port) => Number.isInteger(port) && port > 0 && port <= 65535,
  )
) {
  throw new Error("CodeImpact ports must be between 1 and 65535.");
}
const api = `http://127.0.0.1:${apiPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: webPort,
    strictPort: true,
    proxy: {
      "/api": api,
      "/health": api,
      "/docs": api,
      "/openapi.json": api,
    },
  },
});
