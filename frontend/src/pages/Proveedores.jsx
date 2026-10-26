import ListadoABM from "../components/ListadoABM.jsx";

// Proveedores. Los ven y modifican la administración y compras (la ruta ya lo restringe).
export default function Proveedores() {
  return (
    <ListadoABM
      titulo="Proveedores"
      singular="proveedor"
      articulo="el"
      ruta="/api/proveedores/"
      campoActivo="activo"
      puedeEditar
      nombreDe={(p) => `"${p.nombre}"`}
      columnas={[
        { clave: "nombre", titulo: "Nombre" },
        { clave: "contacto", titulo: "Contacto" },
        { clave: "telefono", titulo: "Teléfono" },
        { clave: "email", titulo: "Email" },
      ]}
      campos={[
        { clave: "nombre", titulo: "Nombre", requerido: true, maximo: 150 },
        { clave: "contacto", titulo: "Contacto", maximo: 150 },
        { clave: "telefono", titulo: "Teléfono", maximo: 50 },
        { clave: "email", titulo: "Email", tipo: "email", maximo: 150 },
      ]}
      vacio={{ nombre: "", contacto: "", telefono: "", email: "" }}
    />
  );
}
