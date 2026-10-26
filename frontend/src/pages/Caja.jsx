import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiFetch, querystring } from "../api/client.js";
import { erroresPorCampo, mensajeDeError } from "../api/errores.js";
import { sedesActivas } from "../api/sedes.js";
import { useAuth } from "../auth/AuthContext.jsx";
import Mensaje from "../components/Mensaje.jsx";
import Paginacion from "../components/Paginacion.jsx";
import ResumenVentas from "../components/ResumenVentas.jsx";
import { dinero, fechaYHora } from "../utils/formato.js";

// Apertura y cierre de caja. El cajero opera la caja de su sede; la administración elige la sede.
export default function Caja() {
  const { usuario } = useAuth();
  const esAdmin = usuario.rol === "admin";

  const [sedes, setSedes] = useState([]);
  const [sedeId, setSedeId] = useState(esAdmin ? "" : String(usuario.sede ?? ""));
  const [caja, setCaja] = useState(null); // caja abierta de la sede (con totales) o null
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");
  const [cierre, setCierre] = useState(null); // última caja cerrada en esta pantalla

  const [monto, setMonto] = useState("");
  const [errorMonto, setErrorMonto] = useState("");
  const [enviando, setEnviando] = useState(false);

  const [historial, setHistorial] = useState([]);
  const [cantidad, setCantidad] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [abierta, setAbierta] = useState(null); // id de la caja del historial con el resumen desplegado
  const [resumenes, setResumenes] = useState({});

  useEffect(() => {
    if (!esAdmin) return;
    sedesActivas()
      .then(setSedes)
      .catch((e) => setError(mensajeDeError(e)));
  }, [esAdmin]);

  const cargarCaja = useCallback(async () => {
    if (!sedeId) {
      setCaja(null);
      return;
    }
    setCargando(true);
    setError("");
    try {
      setCaja(await apiFetch(`/api/cajas/actual/${querystring({ sede: esAdmin ? sedeId : "" })}`));
    } catch (e) {
      if (e.status === 404) setCaja(null);
      else setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, [sedeId, esAdmin]);

  const cargarHistorial = useCallback(async () => {
    try {
      const datos = await apiFetch(
        `/api/cajas/${querystring({ estado: "cerrada", page: pagina, sede: esAdmin ? sedeId : "" })}`
      );
      setHistorial(datos.results);
      setCantidad(datos.count);
    } catch (e) {
      if (e.status === 404 && pagina > 1) setPagina(pagina - 1);
      else setError(mensajeDeError(e));
    }
  }, [pagina, sedeId, esAdmin]);

  useEffect(() => {
    cargarCaja();
  }, [cargarCaja]);

  useEffect(() => {
    cargarHistorial();
  }, [cargarHistorial]);

  function cambiarSede(valor) {
    setSedeId(valor);
    setPagina(1);
    setCierre(null);
    setAviso("");
    setAbierta(null);
  }

  async function abrirCaja(evento) {
    evento.preventDefault();
    setEnviando(true);
    setError("");
    setErrorMonto("");
    setAviso("");
    setCierre(null);
    try {
      const cuerpo = { monto_apertura: monto === "" ? "0" : monto };
      if (esAdmin) cuerpo.sede = Number(sedeId);
      await apiFetch("/api/cajas/", { method: "POST", body: JSON.stringify(cuerpo) });
      setMonto("");
      setAviso("Caja abierta. Ya se pueden cargar ventas.");
      await cargarCaja();
    } catch (e) {
      const porCampo = erroresPorCampo(e);
      if (porCampo.monto_apertura) setErrorMonto(porCampo.monto_apertura);
      else setError(mensajeDeError(e));
    } finally {
      setEnviando(false);
    }
  }

  async function cerrarCaja() {
    if (!window.confirm("¿Cerrar la caja? Se calculan los totales y ya no se podrán cargar más ventas en ella.")) return;
    setEnviando(true);
    setError("");
    setAviso("");
    try {
      const cerrada = await apiFetch(`/api/cajas/${caja.id}/cerrar/`, { method: "POST" });
      setCierre(cerrada); // la respuesta incluye el resumen de ventas (totales)
      setCaja(null);
      setPagina(1);
      await cargarHistorial();
    } catch (e) {
      setError(mensajeDeError(e));
      await cargarCaja();
    } finally {
      setEnviando(false);
    }
  }

  async function alternarResumen(fila) {
    if (abierta === fila.id) {
      setAbierta(null);
      return;
    }
    setAbierta(fila.id);
    if (!resumenes[fila.id]) {
      try {
        const totales = await apiFetch(`/api/cajas/${fila.id}/totales/`);
        setResumenes((r) => ({ ...r, [fila.id]: totales }));
      } catch (e) {
        setError(mensajeDeError(e));
      }
    }
  }

  const sedeElegida = sedes.find((s) => String(s.id) === sedeId);

  return (
    <section>
      <div className="encabezado-pantalla">
        <h1>Caja</h1>
      </div>

      {esAdmin && (
        <div className="filtros">
          <label>
            Sede
            <select value={sedeId} onChange={(e) => cambiarSede(e.target.value)}>
              <option value="">Elegí una sede…</option>
              {sedes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {!esAdmin && !usuario.sede && <Mensaje tipo="error">Tu usuario no tiene una sede asignada. Pedile a la administración que te la asigne.</Mensaje>}

      <Mensaje tipo="ok">{aviso}</Mensaje>
      <Mensaje tipo="error">{error}</Mensaje>

      {cierre && (
        <div className="panel">
          <h2>Caja cerrada</h2>
          <Mensaje tipo="ok">
            Cerraste la caja de {cierre.sede_nombre}. El efectivo que debería haber es {dinero(cierre.monto_cierre_calculado)}.
          </Mensaje>
          <ResumenVentas totales={cierre.totales} />
        </div>
      )}

      {sedeId && (
        <div className="panel">
          <h2>Caja actual{esAdmin && sedeElegida ? ` — ${sedeElegida.nombre}` : usuario.sede_nombre ? ` — ${usuario.sede_nombre}` : ""}</h2>
          {cargando && !caja && <p className="detalle">Cargando…</p>}

          {!cargando && !caja && (
            <form onSubmit={abrirCaja}>
              <p>No hay una caja abierta en esta sede. Para empezar a cargar ventas, abrila indicando el efectivo con el que arranca.</p>
              <label className={`campo${errorMonto ? " campo-error" : ""}`} style={{ maxWidth: 260 }}>
                <span>Monto de apertura ($)</span>
                <input type="number" min="0" step="0.01" inputMode="decimal" value={monto} onChange={(e) => setMonto(e.target.value)} placeholder="0" />
                {errorMonto && <small>{errorMonto}</small>}
              </label>
              <button type="submit" className="btn btn-primario" disabled={enviando}>
                {enviando ? "Abriendo…" : "Abrir caja"}
              </button>
            </form>
          )}

          {caja && (
            <>
              <p>
                <span className="badge badge-ok">Abierta</span> desde {fechaYHora(caja.fecha_apertura)} por {caja.usuario_nombre}.
              </p>
              <ResumenVentas totales={caja.totales} />
              <div className="form-acciones">
                <Link to="/ventas" className="btn btn-secundario">
                  Cargar ventas
                </Link>
                <button type="button" className="btn btn-peligro" onClick={cerrarCaja} disabled={enviando}>
                  {enviando ? "Cerrando…" : "Cerrar caja"}
                </button>
              </div>
            </>
          )}
        </div>
      )}
      {esAdmin && !sedeId && <p className="detalle">Elegí una sede para ver o abrir su caja. Abajo se ve el historial de cierres de todas las sedes.</p>}

      <h2>Cierres anteriores</h2>
      <div className="tabla-wrap">
        <table className="tabla">
          <thead>
            <tr>
              <th>Apertura</th>
              <th>Cierre</th>
              {esAdmin && <th>Sede</th>}
              <th>Cajero</th>
              <th className="num">Apertura ($)</th>
              <th className="num">Efectivo esperado</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {historial.map((fila) => (
              <FilaCierre key={fila.id} fila={fila} esAdmin={esAdmin} abierta={abierta === fila.id} resumen={resumenes[fila.id]} onAlternar={() => alternarResumen(fila)} />
            ))}
          </tbody>
        </table>
        {historial.length === 0 && <p className="vacio">Todavía no hay cajas cerradas.</p>}
      </div>
      <Paginacion pagina={pagina} cantidad={cantidad} onCambiar={setPagina} />
    </section>
  );
}

function FilaCierre({ fila, esAdmin, abierta, resumen, onAlternar }) {
  return (
    <>
      <tr>
        <td>{fechaYHora(fila.fecha_apertura)}</td>
        <td>{fechaYHora(fila.fecha_cierre)}</td>
        {esAdmin && <td>{fila.sede_nombre}</td>}
        <td>{fila.usuario_nombre}</td>
        <td className="num">{dinero(fila.monto_apertura)}</td>
        <td className="num">{dinero(fila.monto_cierre_calculado)}</td>
        <td className="acciones">
          <button type="button" className="btn btn-secundario btn-chico" onClick={onAlternar}>
            {abierta ? "Ocultar resumen" : "Ver resumen"}
          </button>
        </td>
      </tr>
      {abierta && (
        <tr>
          <td colSpan={esAdmin ? 7 : 6}>{resumen ? <ResumenVentas totales={resumen} /> : "Cargando…"}</td>
        </tr>
      )}
    </>
  );
}
