import { MEDIOS_DE_PAGO, dinero } from "../utils/formato.js";

// Resumen de ventas de una caja (campo `totales` de la API): importes totales y por medio de pago.
export default function ResumenVentas({ totales }) {
  if (!totales) return null;
  return (
    <>
      <div className="kpis">
        <div className="kpi">
          <span>Comprobantes</span>
          <strong>{totales.cantidad_comprobantes}</strong>
        </div>
        <div className="kpi">
          <span>Total de ventas</span>
          <strong>{dinero(totales.total_ventas)}</strong>
        </div>
        <div className="kpi">
          <span>Monto de apertura</span>
          <strong>{dinero(totales.monto_apertura)}</strong>
        </div>
        <div className="kpi">
          <span>Efectivo esperado en caja</span>
          <strong>{dinero(totales.efectivo_esperado)}</strong>
        </div>
      </div>
      <div className="tabla-wrap">
        <table className="tabla">
          <thead>
            <tr>
              <th>Medio de pago</th>
              <th className="num">Comprobantes</th>
              <th className="num">Total</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(MEDIOS_DE_PAGO).map(([clave, etiqueta]) => (
              <tr key={clave}>
                <td>{etiqueta}</td>
                <td className="num">{totales.por_medio_pago[clave]?.cantidad ?? 0}</td>
                <td className="num">{dinero(totales.por_medio_pago[clave]?.total ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="detalle">
        El efectivo esperado es el monto de apertura más las ventas en efectivo. Tarjeta, transferencia y QR no pasan por la caja.
      </p>
    </>
  );
}
