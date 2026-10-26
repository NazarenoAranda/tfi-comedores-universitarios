// Formato de importes y fechas para mostrar en pantalla.

const ZONA = "America/Argentina/Buenos_Aires";

const moneda = new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" });
const fechaHora = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short", timeZone: ZONA });
const soloFecha = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeZone: ZONA });

// La API devuelve los importes como texto ("1500.50"); acá solo se formatean para mostrar.
export function dinero(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  const numero = Number(valor);
  return Number.isNaN(numero) ? "—" : moneda.format(numero);
}

export function fechaYHora(iso) {
  return iso ? fechaHora.format(new Date(iso)) : "—";
}

export function fecha(iso) {
  return iso ? soloFecha.format(new Date(iso)) : "—";
}

// Fecha de hoy (en Argentina) como AAAA-MM-DD, para los filtros.
export function hoyISO() {
  const partes = new Intl.DateTimeFormat("en-CA", { timeZone: ZONA }).format(new Date());
  return partes;
}

export const ROLES = { admin: "Administración", cajero: "Cajero", compras: "Compras" };
export const MEDIOS_DE_PAGO = { efectivo: "Efectivo", tarjeta: "Tarjeta", transferencia: "Transferencia", qr: "QR" };
