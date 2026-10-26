// Aviso en pantalla. tipo: "error" | "ok" | "info".
export default function Mensaje({ tipo = "info", children }) {
  if (!children) return null;
  return (
    <div className={`alerta alerta-${tipo}`} role={tipo === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
