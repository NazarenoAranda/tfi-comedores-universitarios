import { Fragment, useCallback, useEffect, useState } from "react";

import { apiFetch, querystring } from "../api/client.js";
import { erroresPorCampo, mensajeDeError } from "../api/errores.js";
import { proveedoresActivos } from "../api/proveedores.js";
import { sedesActivas } from "../api/sedes.js";
import Mensaje from "../components/Mensaje.jsx";
import Paginacion from "../components/Paginacion.jsx";
import { dinero, fecha, fechaYHora } from "../utils/formato.js";

const ITEM_VACIO = { descripcion: "", cantidad: "1", precio_unitario: "" };
const ESTADOS = { pendiente: "Pendiente", recibido: "Recibido", cancelado: "Cancelado" };
const BADGE = { pendiente: "badge-aviso", recibido: "badge-ok", cancelado: "badge-baja" };
const FILTROS_VACIOS = { estado: "", sede: "", proveedor: "", desde: "", hasta: "" };

// "1500.50" -> 150050 (centavos): evita errores de redondeo al sumar con decimales.
function centavos(texto) {
  const n = Number(texto);
  return Number.isFinite(n) ? Math.round(n * 100) : 0;
}

// Pedidos a proveedores: alta, listado con filtros y cambio de estado (recibir / cancelar).
// Los ven y operan la administración y compras (la ruta ya lo restringe).
export default function Pedidos() {
  const [sedes, setSedes] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  // Formulario de alta
  const [abierto, setAbierto] = useState(false);
  const [proveedor, setProveedor] = useState("");
  const [sede, setSede] = useState("");
  const [items, setItems] = useState([{ ...ITEM_VACIO }]);
  const [enviando, setEnviando] = useState(false);
  const [erroresForm, setErroresForm] = useState({});
  const [errorForm, setErrorForm] = useState("");

  // Listado
  const [filas, setFilas] = useState([]);
  const [cantidad, setCantidad] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [filtros, setFiltros] = useState(FILTROS_VACIOS);
  const [cargando, setCargando] = useState(true);
  const [detalle, setDetalle] = useState(null);
  const [procesando, setProcesando] = useState(null); // id del pedido que cambia de estado

  useEffect(() => {
    Promise.all([sedesActivas(), proveedoresActivos()])
      .then(([s, p]) => {
        setSedes(s);
        setProveedores(p);
      })
      .catch((e) => setError(mensajeDeError(e)));
  }, []);

  const cargarListado = useCallback(async () => {
    setCargando(true);
    try {
      const datos = await apiFetch(`/api/pedidos/${querystring({ ...filtros, page: pagina })}`);
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
    cargarListado();
  }, [cargarListado]);

  const total = items.reduce((suma, i) => suma + centavos(i.precio_unitario) * (Number(i.cantidad) || 0), 0);

  function cambiarItem(indice, campo, valor) {
    setItems(items.map((it, i) => (i === indice ? { ...it, [campo]: valor } : it)));
  }

  function abrirFormulario() {
    setAviso("");
    setErrorForm("");
    setErroresForm({});
    setAbierto(true);
  }

  async function guardar(evento) {
    evento.preventDefault();
    setErrorForm("");
    setErroresForm({});
    setAviso("");
    setEnviando(true);
    try {
      const creado = await apiFetch("/api/pedidos/", {
        method: "POST",
        body: JSON.stringify({
          proveedor: Number(proveedor),
          sede: Number(sede),
          items: items.map((i) => ({ descripcion: i.descripcion.trim(), cantidad: Number(i.cantidad), precio_unitario: i.precio_unitario })),
        }),
      });
      setAviso(`Pedido N.º ${creado.id} registrado a ${creado.proveedor_nombre} por ${dinero(creado.monto_total)}.`);
      setItems([{ ...ITEM_VACIO }]);
      setProveedor("");
      setSede("");
      setAbierto(false);
      setPagina(1);
      await cargarListado();
    } catch (e) {
      setErroresForm(erroresPorCampo(e));
      setErrorForm(mensajeDeError(e));
    } finally {
      setEnviando(false);
    }
  }

  async function cambiarEstado(fila, accion) {
    const texto =
      accion === "recibir"
        ? `¿Marcar como recibido el pedido N.º ${fila.id} a ${fila.proveedor_nombre}?`
        : `¿Cancelar el pedido N.º ${fila.id} a ${fila.proveedor_nombre}? Un pedido cancelado no se puede reactivar.`;
    if (!window.confirm(texto)) return;
    setAviso("");
    setError("");
    setProcesando(fila.id);
    try {
      await apiFetch(`/api/pedidos/${fila.id}/${accion}/`, { method: "POST" });
      setAviso(`Pedido N.º ${fila.id} ${accion === "recibir" ? "marcado como recibido" : "cancelado"}.`);
      await cargarListado();
    } catch (e) {
      setError(mensajeDeError(e));
      await cargarListado(); // por si otra persona ya lo cambió
    } finally {
      setProcesando(null);
    }
  }

  function cambiarFiltro(campo, valor) {
    setPagina(1);
    setFiltros({ ...filtros, [campo]: valor });
  }

  return (
    <section>
      <div className="encabezado-pantalla">
        <h1>Pedidos a proveedores</h1>
        {!abierto && (
          <button type="button" className="btn btn-primario" onClick={abrirFormulario}>
            + Nuevo pedido
          </button>
        )}
      </div>

      <Mensaje tipo="ok">{aviso}</Mensaje>
      <Mensaje tipo="error">{error}</Mensaje>

      {abierto && (
        <form className="panel" onSubmit={guardar}>
          <h2>Nuevo pedido</h2>
          <Mensaje tipo="error">{errorForm}</Mensaje>
          <div className="form-grid">
            <label className={`campo${erroresForm.proveedor ? " campo-error" : ""}`}>
              <span>Proveedor *</span>
              <select value={proveedor} onChange={(e) => setProveedor(e.target.value)} required>
                <option value="">Elegí un proveedor…</option>
                {proveedores.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </select>
            </label>
            <label className={`campo${erroresForm.sede ? " campo-error" : ""}`}>
              <span>Sede que recibe el pedido *</span>
              <select value={sede} onChange={(e) => setSede(e.target.value)} required>
                <option value="">Elegí una sede…</option>
                {sedes.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {items.map((item, indice) => (
            <div className="form-grid item-fila" key={indice}>
              <label className="campo">
                <span>{indice === 0 ? "Producto *" : " "}</span>
                <input value={item.descripcion} maxLength={150} required placeholder="Ej.: Harina 000 x 25 kg" aria-label={`Producto ${indice + 1}`} onChange={(e) => cambiarItem(indice, "descripcion", e.target.value)} />
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
            <strong>Total del pedido: {dinero(total / 100)}</strong>
          </div>
          <div className="form-acciones">
            <button type="submit" className="btn btn-primario" disabled={enviando}>
              {enviando ? "Guardando…" : "Registrar pedido"}
            </button>
            <button type="button" className="btn btn-secundario" disabled={enviando} onClick={() => setAbierto(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div className="filtros">
        <label>
          Estado
          <select value={filtros.estado} onChange={(e) => cambiarFiltro("estado", e.target.value)}>
            <option value="">Todos</option>
            {Object.entries(ESTADOS).map(([clave, etiqueta]) => (
              <option key={clave} value={clave}>
                {etiqueta}
              </option>
            ))}
          </select>
        </label>
        <label>
          Proveedor
          <select value={filtros.proveedor} onChange={(e) => cambiarFiltro("proveedor", e.target.value)}>
            <option value="">Todos</option>
            {proveedores.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </select>
        </label>
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
        <label>
          Desde
          <input type="date" value={filtros.desde} max={filtros.hasta || undefined} onChange={(e) => cambiarFiltro("desde", e.target.value)} />
        </label>
        <label>
          Hasta
          <input type="date" value={filtros.hasta} min={filtros.desde || undefined} onChange={(e) => cambiarFiltro("hasta", e.target.value)} />
        </label>
        <button type="button" className="btn btn-secundario" onClick={() => { setPagina(1); setFiltros(FILTROS_VACIOS); }}>
          Limpiar filtros
        </button>
      </div>

      <div className="tabla-wrap">
        <table className="tabla">
          <thead>
            <tr>
              <th>N.º</th>
              <th>Fecha</th>
              <th>Proveedor</th>
              <th>Sede</th>
              <th>Estado</th>
              <th>Recibido</th>
              <th className="num">Total</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <Fragment key={fila.id}>
                <tr>
                  <td>{fila.id}</td>
                  <td>{fecha(fila.fecha_pedido)}</td>
                  <td>{fila.proveedor_nombre}</td>
                  <td>{fila.sede_nombre}</td>
                  <td>
                    <span className={`badge ${BADGE[fila.estado]}`}>{ESTADOS[fila.estado]}</span>
                  </td>
                  <td>{fila.fecha_recibido ? fechaYHora(fila.fecha_recibido) : "—"}</td>
                  <td className="num">{dinero(fila.monto_total)}</td>
                  <td className="acciones">
                    <button type="button" className="btn btn-secundario btn-chico" onClick={() => setDetalle(detalle === fila.id ? null : fila.id)}>
                      {detalle === fila.id ? "Ocultar" : "Ver detalle"}
                    </button>
                    {fila.estado === "pendiente" && (
                      <>
                        <button type="button" className="btn btn-primario btn-chico" disabled={procesando === fila.id} onClick={() => cambiarEstado(fila, "recibir")}>
                          Recibido
                        </button>
                        <button type="button" className="btn btn-peligro btn-chico" disabled={procesando === fila.id} onClick={() => cambiarEstado(fila, "cancelar")}>
                          Cancelar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
                {detalle === fila.id && (
                  <tr>
                    <td colSpan={8}>
                      <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {fila.items.map((i) => (
                          <li key={i.id}>
                            {i.cantidad} × {i.descripcion} — {dinero(i.precio_unitario)} c/u = <strong>{dinero(i.subtotal)}</strong>
                          </li>
                        ))}
                      </ul>
                      <p className="detalle" style={{ marginBottom: 0 }}>
                        Cargado por {fila.usuario_nombre} el {fechaYHora(fila.fecha_pedido)}.
                      </p>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
        {cargando && filas.length === 0 && <p className="vacio">Cargando…</p>}
        {!cargando && filas.length === 0 && <p className="vacio">No hay pedidos con esos filtros.</p>}
      </div>
      <Paginacion pagina={pagina} cantidad={cantidad} onCambiar={setPagina} />
    </section>
  );
}
