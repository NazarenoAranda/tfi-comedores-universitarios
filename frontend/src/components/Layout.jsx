import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";
import { seccionesPara } from "../menu.js";
import { ROLES } from "../utils/formato.js";

// Estructura común de las pantallas con sesión iniciada: encabezado con el menú y contenido.
export default function Layout() {
  const { usuario, logout } = useAuth();
  const navegar = useNavigate();

  async function salir() {
    await logout();
    navegar("/login", { replace: true });
  }

  return (
    <div className="app">
      <header className="header">
        <span className="brand">Gestión de Caja · Comedores Universitarios</span>
        <nav className="nav" aria-label="Menú principal">
          {seccionesPara(usuario.rol).map((s) => (
            <NavLink key={s.ruta} to={s.ruta} end={s.ruta === "/"}>
              {s.etiqueta}
            </NavLink>
          ))}
        </nav>
        <div className="sesion">
          <span className="sesion-datos">
            {usuario.nombre}
            <small>
              {ROLES[usuario.rol] || usuario.rol}
              {usuario.sede_nombre ? ` · ${usuario.sede_nombre}` : ""}
            </small>
          </span>
          <button type="button" className="btn btn-claro btn-chico" onClick={salir}>
            Salir
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
