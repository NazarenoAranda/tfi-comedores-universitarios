import { useCallback, useEffect, useState } from "react";

import { apiFetch, querystring } from "../api/client.js";
import { erroresPorCampo, mensajeDeError } from "../api/errores.js";
import Mensaje from "./Mensaje.jsx";
import Paginacion from "./Paginacion.jsx";

/**
 * Pantalla de listado + formulario (alta, modificación y baja lógica) para un recurso de la API.
 *
 * Props:
 *  - titulo, singular: textos de la pantalla ("Sedes", "sede").
 *  - ruta: dirección de la API ("/api/sedes/").
 *  - campoActivo: nombre del campo booleano de baja lógica ("activa" o "activo").
 *  - columnas: [{ clave, titulo, mostrar?(fila) }].
 *  - campos: [{ clave, titulo, tipo?, requerido? }] del formulario.
 *  - vacio: objeto con los valores iniciales del formulario.
 *  - puedeEditar: false para los roles de solo consulta.
 *  - nombreDe(fila): texto para los mensajes de confirmación.
 */
export default function ListadoABM({ titulo, singular, articulo = "la", ruta, campoActivo, columnas, campos, vacio, puedeEditar, nombreDe }) {
  const [filas, setFilas] = useState([]);
  const [cantidad, setCantidad] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [busqueda, setBusqueda] = useState("");
  const [textoBusqueda, setTextoBusqueda] = useState("");
  const [estado, setEstado] = useState("true"); // "true" | "false" | "" (todos)
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState("");

  const [formulario, setFormulario] = useState(null); // null = cerrado; {id?, ...valores}
  const [erroresForm, setErroresForm] = useState({});
  const [errorForm, setErrorForm] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      const datos = await apiFetch(
        ruta + querystring({ page: pagina, search: busqueda, [campoActivo]: estado })
      );
      setFilas(datos.results);
      setCantidad(datos.count);
    } catch (e) {
      // Si se pidió una página que ya no existe (por ejemplo tras dar de baja el último de la página), se vuelve a la anterior.
      if (e.status === 404 && pagina > 1) setPagina(pagina - 1);
      else setError(mensajeDeError(e));
    } finally {
      setCargando(false);
    }
  }, [ruta, campoActivo, pagina, busqueda, estado]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  function abrirNuevo() {
    setAviso("");
    setErroresForm({});
    setErrorForm("");
    setFormulario({ ...vacio });
  }

  function abrirEdicion(fila) {
    setAviso("");
    setErroresForm({});
    setErrorForm("");
    const valores = { id: fila.id };
    campos.forEach((c) => {
      valores[c.clave] = fila[c.clave] ?? "";
    });
    setFormulario(valores);
  }

  async function guardar(evento) {
    evento.preventDefault();
    setGuardando(true);
    setErroresForm({});
    setErrorForm("");
    const cuerpo = {};
    campos.forEach((c) => {
      cuerpo[c.clave] = typeof formulario[c.clave] === "string" ? formulario[c.clave].trim() : formulario[c.clave];
    });
    try {
      if (formulario.id) {
        await apiFetch(`${ruta}${formulario.id}/`, { method: "PATCH", body: JSON.stringify(cuerpo) });
        setAviso(`Se guardaron los cambios de ${nombreDe(cuerpo)}.`);
      } else {
        await apiFetch(ruta, { method: "POST", body: JSON.stringify(cuerpo) });
        setAviso(`Se creó ${articulo === "la" ? "la" : "el"} ${singular} ${nombreDe(cuerpo)}.`);
      }
      setFormulario(null);
      setPagina(1);
      await cargar();
    } catch (e) {
      const porCampo = erroresPorCampo(e);
      setErroresForm(porCampo);
      // Si el error no es de un campo concreto, se muestra arriba del formulario.
      setErrorForm(Object.keys(porCampo).length ? "Revisá los datos marcados." : mensajeDeError(e));
    } finally {
      setGuardando(false);
    }
  }

  async function cambiarEstado(fila, activar) {
    setAviso("");
    setError("");
    if (!activar && !window.confirm(`¿Dar de baja ${articulo} ${singular} ${nombreDe(fila)}? No se borra: queda inactiv${articulo === "la" ? "a" : "o"} y se conserva su historial.`)) {
      return;
    }
    try {
      if (activar) {
        await apiFetch(`${ruta}${fila.id}/`, { method: "PATCH", body: JSON.stringify({ [campoActivo]: true }) });
        setAviso(`Se reactivó ${articulo} ${singular} ${nombreDe(fila)}.`);
      } else {
        await apiFetch(`${ruta}${fila.id}/`, { method: "DELETE" });
        setAviso(`Se dio de baja ${articulo} ${singular} ${nombreDe(fila)}.`);
      }
      await cargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  function buscar(evento) {
    evento.preventDefault();
    setPagina(1);
    setBusqueda(textoBusqueda.trim());
  }

  return (
    <section>
      <div className="encabezado-pantalla">
        <h1>{titulo}</h1>
        {puedeEditar && !formulario && (
          <button type="button" className="btn btn-primario" onClick={abrirNuevo}>
            + Nuev{articulo === "la" ? "a" : "o"} {singular}
          </button>
        )}
      </div>
      {!puedeEditar && <p className="detalle">Solo consulta: tu rol no puede modificar este listado.</p>}

      <Mensaje tipo="ok">{aviso}</Mensaje>
      <Mensaje tipo="error">{error}</Mensaje>

      {formulario && (
        <form className="panel" onSubmit={guardar}>
          <h2>{formulario.id ? `Modificar ${singular}` : `Nuev${articulo === "la" ? "a" : "o"} ${singular}`}</h2>
          <Mensaje tipo="error">{errorForm}</Mensaje>
          <div className="form-grid">
            {campos.map((c) => (
              <label key={c.clave} className={`campo${erroresForm[c.clave] ? " campo-error" : ""}`}>
                <span>
                  {c.titulo}
                  {c.requerido ? " *" : ""}
                </span>
                <input
                  type={c.tipo || "text"}
                  value={formulario[c.clave]}
                  required={c.requerido}
                  maxLength={c.maximo}
                  onChange={(e) => setFormulario({ ...formulario, [c.clave]: e.target.value })}
                />
                {erroresForm[c.clave] && <small>{erroresForm[c.clave]}</small>}
              </label>
            ))}
          </div>
          <div className="form-acciones">
            <button type="submit" className="btn btn-primario" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar"}
            </button>
            <button type="button" className="btn btn-secundario" onClick={() => setFormulario(null)} disabled={guardando}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <form className="filtros" onSubmit={buscar}>
        <label>
          Buscar
          <input type="search" value={textoBusqueda} onChange={(e) => setTextoBusqueda(e.target.value)} placeholder="Texto…" />
        </label>
        <label>
          Mostrar
          <select
            value={estado}
            onChange={(e) => {
              setPagina(1);
              setEstado(e.target.value);
            }}
          >
            <option value="true">Activos</option>
            <option value="false">Dados de baja</option>
            <option value="">Todos</option>
          </select>
        </label>
        <button type="submit" className="btn btn-secundario">
          Buscar
        </button>
      </form>

      <div className="tabla-wrap">
        <table className="tabla">
          <thead>
            <tr>
              {columnas.map((c) => (
                <th key={c.clave}>{c.titulo}</th>
              ))}
              <th>Estado</th>
              {puedeEditar && <th />}
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <tr key={fila.id} className={fila[campoActivo] ? "" : "inactiva"}>
                {columnas.map((c) => (
                  <td key={c.clave}>{(c.mostrar ? c.mostrar(fila) : fila[c.clave]) || "—"}</td>
                ))}
                <td>
                  <span className={`badge ${fila[campoActivo] ? "badge-ok" : "badge-baja"}`}>{fila[campoActivo] ? "Activo" : "De baja"}</span>
                </td>
                {puedeEditar && (
                  <td className="acciones">
                    <button type="button" className="btn btn-secundario btn-chico" onClick={() => abrirEdicion(fila)}>
                      Modificar
                    </button>
                    {fila[campoActivo] ? (
                      <button type="button" className="btn btn-peligro btn-chico" onClick={() => cambiarEstado(fila, false)}>
                        Dar de baja
                      </button>
                    ) : (
                      <button type="button" className="btn btn-secundario btn-chico" onClick={() => cambiarEstado(fila, true)}>
                        Reactivar
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        {cargando && filas.length === 0 && <p className="vacio">Cargando…</p>}
        {!cargando && filas.length === 0 && !error && <p className="vacio">No hay resultados.</p>}
      </div>
      <Paginacion pagina={pagina} cantidad={cantidad} onCambiar={setPagina} />
    </section>
  );
}
