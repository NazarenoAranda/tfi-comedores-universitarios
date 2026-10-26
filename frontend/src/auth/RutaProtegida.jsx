import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./AuthContext.jsx";

// Deja pasar solo a quien inició sesión (y, si se indican `roles`, a quien tenga uno de esos roles).
export default function RutaProtegida({ roles }) {
  const { usuario, cargando, salioAPropósito } = useAuth();
  const ubicacion = useLocation();

  if (cargando) return <p className="cargando">Verificando sesión…</p>;
  if (!usuario) return <Navigate to="/login" replace state={salioAPropósito ? undefined : { desde: ubicacion.pathname }} />;
  if (roles && !roles.includes(usuario.rol)) {
    return (
      <section>
        <h1>Sin acceso</h1>
        <p>Tu rol no tiene permiso para ver esta pantalla.</p>
      </section>
    );
  }
  return <Outlet />;
}
