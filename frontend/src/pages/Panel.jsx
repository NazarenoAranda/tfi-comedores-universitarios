import { useCallback, useEffect, useState } from "react";

import { apiFetch, querystring } from "../api/client.js";
import { mensajeDeError } from "../api/errores.js";
import { sedesActivas } from "../api/sedes.js";
import Mensaje from "../components/Mensaje.jsx";
import { MEDIOS_DE_PAGO, dinero, hoyISO } from "../utils/formato.js";

const ESTADOS_PEDIDO = { pendiente: "Pendientes", recibido: "Recibidos", cancelado: "Cancelados" };

// Fecha AAAA-MM-DD de hace `dias` días (se calcula sobre la fecha de hoy en Argentina).
function haceDias(dias) {
  const base = new Date(`${hoyISO()}T12:00:00Z`);
  base.setUTCDate(base.getUTCDate() - dias);
  return base.toISOString().slice(0, 10);
}

const ATAJOS = [
  { id: "hoy", etiqueta: "Hoy", rango: () => ({ desde: hoyISO(), hasta: hoyISO() }) },
  { id: "7", etiqueta: "Últimos 7 días", rango: () => ({ desde: haceDias(6), hasta: hoyISO() }) },
  { id: "30", etiqueta: "Últimos 30 días", rango: () => ({ desde: haceDias(29), hasta: hoyISO() }) },
  { id: "todo", etiqueta: "Todo el período", rango: () => ({ desde: "", hasta: "" }) },
];

function claseResultado(valor) {
  return Number(valor) < 0 ? "resultado-negativo" : "resultado-positivo";
}

// Panel consolidado (solo administración): ventas y pedidos por sede y de toda la cadena.
export default function Panel() {
  const [sedes, setSedes] = useState([]);
  const [filtros, setFiltros] = useState({ sede: "", ...ATAJOS[2].rango() });
  const [atajo, setAtajo] = useState("30");
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    sedesActivas().then(setSedes).catch((e) => setError(mensajeDeError(e)));
  }, []);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      setDatos(await apiFetch(`/api/dashboard/resumen/${querystring(filtros)}`));
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, [filtros]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function elegirAtajo(a) {
    setAtajo(a.id);
    setFiltros({ ...filtros, ...a.rango() });
  }

  function cambiarFecha(campo, valor) {
    setAtajo("");
    setFiltros({ ...filtros, [campo]: valor });
  }

  const consolidado = datos?.consolidado;
  const porSede = datos?.por_sede ?? [];
  // La barra más larga es el mayor importe entre todas las sedes (ventas o pedidos).
  const maximo = Math.max(1, ...porSede.flatMap((s) => [Number(s.ventas.total), Number(s.pedidos.total)]));

  return (
    <section>
      <div className="encabezado-pantalla">
        <h1>Panel consolidado</h1>
      </div>
      <p className="detalle">Ventas y pedidos de todas las sedes. Los pedidos cancelados no se cuentan en los totales.</p>

      <div className="filtros">
        <div className="atajos" role="group" aria-label="Períodos rápidos">
          {ATAJOS.map((a) => (
            <button key={a.id} type="button" className={`btn btn-chico ${atajo === a.id ? "btn-primario" : "btn-secundario"}`} onClick={() => elegirAtajo(a)}>
              {a.etiqueta}
            </button>
          ))}
        </div>
        <label>
          Desde
          <input type="date" value={filtros.desde} max={filtros.hasta || undefined} onChange={(e) => cambiarFecha("desde", e.target.value)} />
        </label>
        <label>
          Hasta
          <input type="date" value={filtros.hasta} min={filtros.desde || undefined} onChange={(e) => cambiarFecha("hasta", e.target.value)} />
        </label>
        <label>
          Sede
          <select value={filtros.sede} onChange={(e) => setFiltros({ ...filtros, sede: e.target.value })}>
            <option value="">Todas las sedes</option>
            {sedes.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </label>
      </div>

      <Mensaje tipo="error">{error}</Mensaje>
      {cargando && !datos && <p className="cargando">Calculando…</p>}

      {consolidado && (
        <div style={{ opacity: cargando ? 0.6 : 1 }}>
          <div className="kpis kpis-grandes">
            <div className="kpi">
              <span>Ventas ({consolidado.ventas.cantidad} comprobantes)</span>
              <strong>{dinero(consolidado.ventas.total)}</strong>
            </div>
            <div className="kpi">
              <span>Pedidos a proveedores ({consolidado.pedidos.cantidad})</span>
              <strong>{dinero(consolidado.pedidos.total)}</strong>
            </div>
            <div className="kpi">
              <span>Resultado (ventas − pedidos)</span>
              <strong className={claseResultado(consolidado.resultado)}>{dinero(consolidado.resultado)}</strong>
            </div>
          </div>

          <div className="dos-columnas">
            <div>
              <h2>Ventas por medio de pago</h2>
              <div className="tabla-wrap">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Medio</th>
                      <th className="num">Comprobantes</th>
                      <th className="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(MEDIOS_DE_PAGO).map(([clave, etiqueta]) => (
                      <tr key={clave}>
                        <td>{etiqueta}</td>
                        <td className="num">{consolidado.ventas.por_medio_pago[clave].cantidad}</td>
                        <td className="num">{dinero(consolidado.ventas.por_medio_pago[clave].total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h2>Pedidos por estado</h2>
              <div className="tabla-wrap">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th>Estado</th>
                      <th className="num">Pedidos</th>
                      <th className="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(ESTADOS_PEDIDO).map(([clave, etiqueta]) => (
                      <tr key={clave} className={clave === "cancelado" ? "inactiva" : ""}>
                        <td>{etiqueta}</td>
                        <td className="num">{consolidado.pedidos.por_estado[clave].cantidad}</td>
                        <td className="num">{dinero(consolidado.pedidos.por_estado[clave].total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <h2>Por sede</h2>
          <div className="tabla-wrap">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Sede</th>
                  <th className="num">Ventas</th>
                  <th className="num">Total ventas</th>
                  <th className="num">Pedidos</th>
                  <th className="num">Total pedidos</th>
                  <th className="num">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {porSede.map((s) => (
                  <tr key={s.sede}>
                    <td>{s.sede_nombre}</td>
                    <td className="num">{s.ventas.cantidad}</td>
                    <td className="num">{dinero(s.ventas.total)}</td>
                    <td className="num">{s.pedidos.cantidad}</td>
                    <td className="num">{dinero(s.pedidos.total)}</td>
                    <td className={`num ${claseResultado(s.resultado)}`}>{dinero(s.resultado)}</td>
                  </tr>
                ))}
                <tr className="fila-total">
                  <td>Total consolidado</td>
                  <td className="num">{consolidado.ventas.cantidad}</td>
                  <td className="num">{dinero(consolidado.ventas.total)}</td>
                  <td className="num">{consolidado.pedidos.cantidad}</td>
                  <td className="num">{dinero(consolidado.pedidos.total)}</td>
                  <td className={`num ${claseResultado(consolidado.resultado)}`}>{dinero(consolidado.resultado)}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {porSede.length > 0 && (
            <>
              <h2>Ventas y pedidos por sede</h2>
              <div className="panel grafico" role="img" aria-label="Comparación de ventas y pedidos por sede">
                <div className="leyenda">
                  <span><i className="muestra muestra-ventas" /> Ventas</span>
                  <span><i className="muestra muestra-pedidos" /> Pedidos</span>
                </div>
                {porSede.map((s) => (
                  <div className="grafico-fila" key={s.sede}>
                    <div className="grafico-nombre">{s.sede_nombre}</div>
                    <div className="grafico-barras">
                      <div className="barra-linea">
                        <div className="barra barra-ventas" style={{ width: `${(Number(s.ventas.total) / maximo) * 100}%` }} />
                        <span>{dinero(s.ventas.total)}</span>
                      </div>
                      <div className="barra-linea">
                        <div className="barra barra-pedidos" style={{ width: `${(Number(s.pedidos.total) / maximo) * 100}%` }} />
                        <span>{dinero(s.pedidos.total)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          {porSede.length === 0 && <p className="vacio">No hay sedes para mostrar.</p>}
        </div>
      )}
    </section>
  );
}
