import { Fragment, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch, querystring } from "../api/client.js";
import { erroresPorCampo, mensajeDeError } from "../api/errores.js";
import { sedesActivas } from "../api/sedes.js";
import { useAuth } from "../auth/AuthContext.jsx";
import Mensaje from "../components/Mensaje.jsx";
import Paginacion from "../components/Paginacion.jsx";
import { MEDIOS_DE_PAGO, dinero, fechaYHora } from "../utils/formato.js";

const ITEM_VACIO = { descripcion: "", cantidad: "1", precio_unitario: "" };

// "1500.50" -> 150050 (centavos): evita errores de redondeo al sumar con decimales.
function centavos(texto) {
  const n = Number(texto);
  return Number.isFinite(n) ? Math.round(n * 100) : 0;
}

// Cargar ventas (comprobantes) en la caja abierta y listarlas con filtros.
export default function Ventas() {
  const { usuario } = useAuth();
  const esAdmin = usuario.rol === "admin";

  const [sedes, setSedes] = useState([]);
  const [cajaAbierta, setCajaAbierta] = useState(undefined); // cajero: su caja abierta; undefined = cargando; null = no hay
  const [cajasAbiertas, setCajasAbiertas] = useState([]); // admin: cajas abiertas para elegir
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  // Formulario de alta
  const [medio, setMedio] = useState("efectivo");
  const [modo, setModo] = useState("items"); // "items" | "total"
  const [items, setItems] = useState([{ ...ITEM_VACIO }]);
  const [montoTotal, setMontoTotal] = useState("");
  const [cajaElegida, setCajaElegida] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erroresForm, setErroresForm] = useState({});
  const [errorForm, setErrorForm] = useState("");

  // Listado
  const [filas, setFilas] = useState([]);
  const [cantidad, setCantidad] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [filtros, setFiltros] = useState({ sede: "", medio_pago: "", desde: "", hasta: "" });
  const [cargando, setCargando] = useState(true);
  const [detalle, setDetalle] = useState(null);

  const cargarCajas = useCallback(async () => {
    try {
      if (esAdmin) {
        const datos = await apiFetch("/api/cajas/?estado=abierta");
        setCajasAbiertas(datos.results);
        setCajaElegida((actual) => (datos.results.some((c) => String(c.id) === actual) ? actual : datos.results[0] ? String(datos.results[0].id) : ""));
      } else {
        try {
          setCajaAbierta(await apiFetch("/api/cajas/actual/"));
        } catch (e) {
          if (e.status === 404) setCajaAbierta(null);
          else throw e;
        }
      }
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }, [esAdmin]);

  const cargarListado = useCallback(async () => {
    setCargando(true);
    try {
      const datos = await apiFetch(`/api/comprobantes/${querystring({ ...filtros, page: pagina })}`);
      setFilas(datos.results);
      setCantidad(datos.count);
    } catch (e) {
      if (e.status === 404 && pagina > 1) setPagina(pagina - 1);
      else setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, [filtros, pagina]);

  useEffect(() => {
    cargarCajas();
    if (esAdmin) sedesActivas().then(setSedes).catch((e) => setError(mensajeDeError(e)));
  }, [cargarCajas, esAdmin]);

  useEffect(() => {
    cargarListado();
  }, [cargarListado]);

  const totalItems = items.reduce((suma, i) => suma + centavos(i.precio_unitario) * (Number(i.cantidad) || 0), 0);
  const hayCajaParaCargar = esAdmin ? cajasAbiertas.length > 0 : Boolean(cajaAbierta);

  function cambiarItem(indice, campo, valor) {
    setItems(items.map((it, i) => (i === indice ? { ...it, [campo]: valor } : it)));
  }

  async function guardar(evento) {
    evento.preventDefault();
    setErrorForm("");
    setErroresForm({});
    setAviso("");
    const cuerpo = { medio_pago: medio };
    if (esAdmin) cuerpo.caja = Number(cajaElegida);
    if (modo === "items") {
      cuerpo.items = items.map((i) => ({
        descripcion: i.descripcion.trim(),
        cantidad: Number(i.cantidad),
        precio_unitario: i.precio_unitario,
      }));
    } else {
      cuerpo.monto_total = montoTotal;
    }
    setEnviando(true);
    try {
      const creado = await apiFetch("/api/comprobantes/", { method: "POST", body: JSON.stringify(cuerpo) });
      setAviso(`Venta registrada: ${dinero(creado.monto_total)} (${MEDIOS_DE_PAGO[creado.medio_pago]}).`);
      setItems([{ ...ITEM_VACIO }]);
      setMontoTotal("");
      setPagina(1);
      await cargarListado();
    } catch (e) {
      const porCampo = erroresPorCampo(e);
      setErroresForm(porCampo);
      setErrorForm(mensajeDeError(e));
      // Si la caja se cerró mientras tanto, se actualiza el estado de la pantalla.
      if (porCampo.caja) cargarCajas();
    } finally {
      setEnviando(false);
    }
  }

  function cambiarFiltro(campo, valor) {
    setPagina(1);
    setFiltros({ ...filtros, [campo]: valor });
  }

  return (
    <section>
      <div className="encabezado-pantalla">
        <h1>Ventas</h1>
      </div>
      <Mensaje tipo="ok">{aviso}</Mensaje>
      <Mensaje tipo="error">{error}</Mensaje>

      <form className="panel" onSubmit={guardar}>
        <h2>Cargar una venta</h2>

        {!esAdmin && cajaAbierta === null && (
          <Mensaje tipo="info">
            No hay una caja abierta en tu sede, así que no se pueden cargar ventas. <Link to="/caja">Abrir la caja</Link>
          </Mensaje>
        )}
        {esAdmin && cajasAbiertas.length === 0 && (
          <Mensaje tipo="info">
            No hay ninguna caja abierta. Las ventas se cargan en una caja abierta: <Link to="/caja">abrir una caja</Link>.
          </Mensaje>
        )}
        <Mensaje tipo="error">{errorForm}</Mensaje>

        <fieldset disabled={!hayCajaParaCargar || enviando} style={{ border: 0, padding: 0, margin: 0 }}>
          <div className="form-grid">
            {esAdmin && (
              <label className={`campo${erroresForm.caja ? " campo-error" : ""}`}>
                <span>Caja *</span>
                <select value={cajaElegida} onChange={(e) => setCajaElegida(e.target.value)} required>
                  {cajasAbiertas.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.sede_nombre} (abierta {fechaYHora(c.fecha_apertura)})
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="campo">
              <span>Medio de pago *</span>
              <select value={medio} onChange={(e) => setMedio(e.target.value)}>
                {Object.entries(MEDIOS_DE_PAGO).map(([clave, etiqueta]) => (
                  <option key={clave} value={clave}>
                    {etiqueta}
                  </option>
                ))}
              </select>
            </label>
            <label className="campo">
              <span>Cómo cargar el importe</span>
              <select value={modo} onChange={(e) => setModo(e.target.value)}>
                <option value="items">Detallando los productos</option>
                <option value="total">Solo el monto total</option>
              </select>
            </label>
          </div>

          {modo === "items" ? (
            <>
              {items.map((item, indice) => (
                <div className="form-grid item-fila" key={indice}>
                  <label className="campo">
                    <span>{indice === 0 ? "Producto *" : " "}</span>
                    <input value={item.descripcion} maxLength={150} required placeholder="Ej.: Menú del día" aria-label={`Producto ${indice + 1}`} onChange={(e) => cambiarItem(indice, "descripcion", e.target.value)} />
                  </label>
                  <label className="campo">
                    <span>{indice === 0 ? "Cantidad *" : " "}</span>
                    <input type="number" min="1" step="1" required value={item.cantidad} aria-label={`Cantidad ${indice + 1}`} onChange={(e) => cambiarItem(indice, "cantidad", e.target.value)} />
                  </label>
                  <label className="campo">
                    <span>{indice === 0 ? "Precio unitario ($) *" : " "}</span>
                    <input type="number" min="0" step="0.01" required value={item.precio_unitario} aria-label={`Precio ${indice + 1}`} onChange={(e) => cambiarItem(indice, "precio_unitario", e.target.value)} />
                  </label>
                  <div className="campo">
                    <span>&nbsp;</span>
                    <button type="button" className="btn btn-peligro btn-chico" disabled={items.length === 1} onClick={() => setItems(items.filter((_, i) => i !== indice))} aria-label={`Quitar producto ${indice + 1}`}>
                      Quitar
                    </button>
                  </div>
                </div>
              ))}
              {erroresForm.items && <p className="detalle" style={{ color: "var(--color-error)" }}>{erroresForm.items}</p>}
              <div className="form-acciones" style={{ alignItems: "center", marginBottom: 14 }}>
                <button type="button" className="btn btn-secundario btn-chico" disabled={items.length >= 100} onClick={() => setItems([...items, { ...ITEM_VACIO }])}>
                  + Agregar producto
                </button>
                <strong>Total: {dinero(totalItems / 100)}</strong>
              </div>
            </>
          ) : (
            <label className={`campo${erroresForm.monto_total ? " campo-error" : ""}`} style={{ maxWidth: 260 }}>
              <span>Monto total ($) *</span>
              <input type="number" min="0.01" step="0.01" required value={montoTotal} onChange={(e) => setMontoTotal(e.target.value)} />
              {erroresForm.monto_total && <small>{erroresForm.monto_total}</small>}
            </label>
          )}

          <button type="submit" className="btn btn-primario">
            {enviando ? "Guardando…" : "Registrar venta"}
          </button>
        </fieldset>
      </form>

      <h2>Comprobantes</h2>
      <div className="filtros">
        {esAdmin && (
          <label>
            Sede
            <select value={filtros.sede} onChange={(e) => cambiarFiltro("sede", e.target.value)}>
              <option value="">Todas</option>
              {sedes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Medio de pago
          <select value={filtros.medio_pago} onChange={(e) => cambiarFiltro("medio_pago", e.target.value)}>
            <option value="">Todos</option>
            {Object.entries(MEDIOS_DE_PAGO).map(([clave, etiqueta]) => (
              <option key={clave} value={clave}>
                {etiqueta}
              </option>
            ))}
          </select>
        </label>
        <label>
          Desde
          <input type="date" value={filtros.desde} max={filtros.hasta || undefined} onChange={(e) => cambiarFiltro("desde", e.target.value)} />
        </label>
        <label>
          Hasta
          <input type="date" value={filtros.hasta} min={filtros.desde || undefined} onChange={(e) => cambiarFiltro("hasta", e.target.value)} />
        </label>
        <button type="button" className="btn btn-secundario" onClick={() => { setPagina(1); setFiltros({ sede: "", medio_pago: "", desde: "", hasta: "" }); }}>
          Limpiar filtros
        </button>
      </div>

      <div className="tabla-wrap">
        <table className="tabla">
          <thead>
            <tr>
              <th>N.º</th>
              <th>Fecha</th>
              {esAdmin && <th>Sede</th>}
              <th>Cargó</th>
              <th>Medio de pago</th>
              <th className="num">Total</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <Fragment key={fila.id}>
                <tr>
                  <td>{fila.id}</td>
                  <td>{fechaYHora(fila.fecha)}</td>
                  {esAdmin && <td>{fila.sede_nombre}</td>}
                  <td>{fila.usuario_nombre}</td>
                  <td>{MEDIOS_DE_PAGO[fila.medio_pago] || fila.medio_pago}</td>
                  <td className="num">{dinero(fila.monto_total)}</td>
                  <td className="acciones">
                    <button type="button" className="btn btn-secundario btn-chico" onClick={() => setDetalle(detalle === fila.id ? null : fila.id)}>
                      {detalle === fila.id ? "Ocultar" : "Ver detalle"}
                    </button>
                  </td>
                </tr>
                {detalle === fila.id && (
                  <tr>
                    <td colSpan={esAdmin ? 7 : 6}>
                      {fila.items.length === 0 ? (
                        <span className="detalle">Se cargó solo el monto total, sin detalle de productos.</span>
                      ) : (
                        <ul style={{ margin: 0, paddingLeft: 18 }}>
                          {fila.items.map((i) => (
                            <li key={i.id}>
                              {i.cantidad} × {i.descripcion} — {dinero(i.precio_unitario)} c/u = <strong>{dinero(i.subtotal)}</strong>
                            </li>
                          ))}
                        </ul>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
        {cargando && filas.length === 0 && <p className="vacio">Cargando…</p>}
        {!cargando && filas.length === 0 && <p className="vacio">No hay comprobantes con esos filtros.</p>}
      </div>
      <Paginacion pagina={pagina} cantidad={cantidad} onCambiar={setPagina} />
    </section>
  );
}
