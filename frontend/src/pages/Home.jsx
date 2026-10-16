import { useEffect, useState } from "react";

import { API_URL, apiFetch } from "../api/client.js";

// Pantalla de inicio provisoria: comprueba que el frontend se comunica con el backend.
export default function Home() {
  const [estado, setEstado] = useState("verificando");

  useEffect(() => {
    let activo = true;
    apiFetch("/api/health/")
      .then((datos) => {
        if (activo) setEstado(datos.status === "ok" ? "conectado" : "error");
      })
      .catch(() => {
        if (activo) setEstado("error");
      });
    return () => {
      activo = false;
    };
  }, []);

  const textos = {
    verificando: "Verificando conexión con el servidor…",
    conectado: "Conectado al servidor correctamente.",
    error: "No se pudo conectar con el servidor.",
  };

  return (
    <section>
      <h1>Sistema de gestión de caja y proveedores</h1>
      <p>
        Cadena de comedores universitarios: ventas, cierre de caja y pedidos a
        proveedores en un solo lugar.
      </p>
      <p className={`estado estado-${estado}`}>{textos[estado]}</p>
      <p className="detalle">
        API: <code>{API_URL}</code>
      </p>
    </section>
  );
}
