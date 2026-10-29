import { apiFetch } from "./client.js";

// Proveedores activos (para los selectores de pedidos). Alcanza con la primera página.
export async function proveedoresActivos() {
  const datos = await apiFetch("/api/proveedores/?activo=true");
  return datos.results;
}
