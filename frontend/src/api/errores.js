// Convierte un error de la API en un texto para mostrar al usuario.
// El backend responde, según el caso: {"campo": ["mensaje"]}, {"detail": "mensaje"} o ["mensaje"].

function aplanar(datos, prefijo = "") {
  if (datos == null) return [];
  if (typeof datos === "string") return [prefijo ? `${prefijo}: ${datos}` : datos];
  if (Array.isArray(datos)) return datos.flatMap((d) => aplanar(d, prefijo));
  if (typeof datos === "object") {
    return Object.entries(datos).flatMap(([clave, valor]) => {
      if (clave === "detail" || clave === "non_field_errors") return aplanar(valor, prefijo);
      const nombre = /^\d+$/.test(clave) ? `${prefijo} ${Number(clave) + 1}`.trim() : clave;
      return aplanar(valor, nombre);
    });
  }
  return [String(datos)];
}

export function mensajeDeError(error) {
  if (!error) return "";
  if (error.status === 0) return "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.";
  if (error.status === 403) return "No tenés permiso para realizar esta acción.";
  if (error.status === 404) return "No se encontró lo que buscabas.";
  if (error.status >= 500) return "El servidor tuvo un problema. Intentá de nuevo en unos minutos.";
  const mensajes = aplanar(error.data);
  return mensajes.length ? mensajes.join(" · ") : "Ocurrió un error inesperado.";
}

// Errores por campo ({"nombre": ["..."]}) para marcarlos en el formulario.
export function erroresPorCampo(error) {
  const datos = error?.data;
  if (!datos || typeof datos !== "object" || Array.isArray(datos)) return {};
  const resultado = {};
  Object.entries(datos).forEach(([campo, valor]) => {
    if (campo === "detail" || campo === "non_field_errors") return;
    resultado[campo] = aplanar(valor).join(" ");
  });
  return resultado;
}
