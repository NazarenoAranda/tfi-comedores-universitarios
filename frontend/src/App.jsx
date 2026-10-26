import { Route, Routes } from "react-router-dom";

import RutaProtegida from "./auth/RutaProtegida.jsx";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import NotFound from "./pages/NotFound.jsx";

// Las pantallas de cada módulo (sedes, proveedores, caja, ventas, pedidos, panel)
// se agregan como nuevas rutas dentro del Layout, con sus roles permitidos.
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RutaProtegida />}>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
    </Routes>
  );
}
