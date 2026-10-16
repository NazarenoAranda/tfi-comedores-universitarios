import { NavLink, Outlet } from "react-router-dom";

// Estructura común de todas las pantallas: encabezado con el menú y contenido.
export default function Layout() {
  return (
    <div className="app">
      <header className="header">
        <span className="brand">Gestión de Caja · Comedores Universitarios</span>
        <nav className="nav">
          <NavLink to="/" end>
            Inicio
          </NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
