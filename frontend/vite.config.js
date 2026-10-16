import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Las variables VITE_* se leen del archivo ".env" de la raíz del repositorio
  // (el mismo que usa el backend). En producción se definen en el panel de Vercel.
  envDir: "..",
  server: {
    port: 5173,
  },
});
