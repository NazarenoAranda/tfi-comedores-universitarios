import ListadoABM from "../components/ListadoABM.jsx";
import { useAuth } from "../auth/AuthContext.jsx";

// Sedes (comedores). Todos los roles las consultan; solo la administración las modifica.
export default function Sedes() {
  const { usuario } = useAuth();
  return (
    <ListadoABM
      titulo="Sedes"
      singular="sede"
      articulo="la"
      ruta="/api/sedes/"
      campoActivo="activa"
      puedeEditar={usuario.rol === "admin"}
      nombreDe={(s) => `"${s.nombre}"`}
      columnas={[
        { clave: "nombre", titulo: "Nombre" },
        { clave: "universidad", titulo: "Universidad" },
        { clave: "direccion", titulo: "Dirección" },
      ]}
      campos={[
        { clave: "nombre", titulo: "Nombre", requerido: true, maximo: 150 },
        { clave: "universidad", titulo: "Universidad", maximo: 150 },
        { clave: "direccion", titulo: "Dirección", maximo: 200 },
      ]}
      vacio={{ nombre: "", universidad: "", direccion: "" }}
    />
  );
}
