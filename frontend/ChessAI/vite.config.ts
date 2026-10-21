import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ["react", "react-dom"],
  },
  optimizeDeps: {
    include: ["react", "react-dom", "react/jsx-dev-runtime"],
    exclude: ["react-chessboard"],
  },
  server: {
    // Send /api/... requests to the FastAPI backend (uvicorn on port 8000)
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
