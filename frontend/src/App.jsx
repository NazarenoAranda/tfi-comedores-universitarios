import { Route, Routes } from "react-router-dom";

import RutaProtegida from "./auth/RutaProtegida.jsx";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import NotFound from "./pages/NotFound.jsx";
import Proveedores from "./pages/Proveedores.jsx";
import Sedes from "./pages/Sedes.jsx";

// Las pantallas de cada módulo se agregan como nuevas rutas dentro del Layout,
// con los roles que pueden verlas (el backend vuelve a controlar los permisos).
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RutaProtegida />}>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="sedes" element={<Sedes />} />
          <Route element={<RutaProtegida roles={["admin", "compras"]} />}>
            <Route path="proveedores" element={<Proveedores />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
    </Routes>
  );
}
