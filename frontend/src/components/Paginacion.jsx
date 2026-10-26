// Controles "Anterior / Siguiente" para los listados paginados de la API (20 por página).
export default function Paginacion({ pagina, cantidad, porPagina = 20, onCambiar }) {
  const total = Math.max(1, Math.ceil(cantidad / porPagina));
  if (cantidad <= porPagina) return null;
  return (
    <div className="paginacion">
      <button type="button" className="btn btn-secundario btn-chico" disabled={pagina <= 1} onClick={() => onCambiar(pagina - 1)}>
        ← Anterior
      </button>
      <span>
        Página {pagina} de {total} · {cantidad} en total
      </span>
      <button type="button" className="btn btn-secundario btn-chico" disabled={pagina >= total} onClick={() => onCambiar(pagina + 1)}>
        Siguiente →
      </button>
    </div>
  );
}
