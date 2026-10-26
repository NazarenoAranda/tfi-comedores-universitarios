import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { seccionesPara } from "../menu.js";
import { ROLES } from "../utils/formato.js";

// Pantalla de inicio: saludo, estado del servidor y accesos a las pantallas del rol.
export default function Home() {
  const { usuario } = useAuth();
  const [estado, setEstado] = useState("verificando");

  useEffect(() => {
    let activo = true;
    apiFetch("/api/health/")
      .then((datos) => activo && setEstado(datos.status === "ok" ? "conectado" : "error"))
      .catch(() => activo && setEstado("error"));
    return () => {
      activo = false;
    };
  }, []);

  const textos = {
    verificando: "Verificando conexión con el servidor…",
    conectado: "Conectado al servidor correctamente.",
    error: "No se pudo conectar con el servidor.",
  };
  const accesos = seccionesPara(usuario.rol).filter((s) => s.ruta !== "/");

  return (
    <section>
      <h1>Hola, {usuario.nombre}</h1>
      <p>
        Ingresaste como <strong>{ROLES[usuario.rol] || usuario.rol}</strong>
        {usuario.sede_nombre ? <> en <strong>{usuario.sede_nombre}</strong></> : null}.
      </p>
      <p className={`estado estado-${estado}`}>{textos[estado]}</p>

      {accesos.length > 0 && (
        <>
          <h2>¿Qué querés hacer?</h2>
          <div className="grid-cards">
            {accesos.map((s) => (
              <Link key={s.ruta} to={s.ruta} className="card card-link">
                <strong>{s.etiqueta}</strong>
                <span>{s.descripcion}</span>
              </Link>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
