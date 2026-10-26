import { apiFetch } from "./client.js";

// Sedes activas (para los selectores de la administración). Son pocas: alcanza la primera página.
export async function sedesActivas() {
  const datos = await apiFetch("/api/sedes/?activa=true");
  return datos.results;
}
