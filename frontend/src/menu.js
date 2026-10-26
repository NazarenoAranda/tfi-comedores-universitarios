// Pantallas de la aplicación: alimentan el menú superior y los accesos de la pantalla de inicio.
// `roles` indica quiénes la ven (admin = administración).

export const SECCIONES = [
  {
    ruta: "/",
    etiqueta: "Inicio",
    roles: ["admin", "cajero", "compras"],
  },
];

export function seccionesPara(rol) {
  return SECCIONES.filter((s) => s.roles.includes(rol));
}
