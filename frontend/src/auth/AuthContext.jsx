import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { apiFetch, clearToken, getToken, setToken, setUnauthorizedHandler } from "../api/client.js";

const AuthContext = createContext(null);

// Guarda quién inició sesión y ofrece login / logout a toda la aplicación.
export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  // true si la persona cerró la sesión a propósito: al volver a ingresar no se la lleva a la última pantalla.
  const [salioAPropósito, setSalioAPropósito] = useState(false);
  // "cargando" solo mientras se verifica un token guardado de una visita anterior.
  const [cargando, setCargando] = useState(() => Boolean(getToken()));

  const cerrarLocal = useCallback(() => {
    clearToken();
    setUsuario(null);
  }, []);

  // Si el servidor rechaza el token en cualquier pantalla, se vuelve al login.
  useEffect(() => {
    setUnauthorizedHandler(cerrarLocal);
    return () => setUnauthorizedHandler(null);
  }, [cerrarLocal]);

  // Al abrir la aplicación con un token guardado, se verifica que siga siendo válido.
  useEffect(() => {
    if (!getToken()) return undefined;
    let activo = true;
    apiFetch("/api/auth/me/")
      .then((datos) => activo && setUsuario(datos))
      .catch((error) => {
        // Sin conexión no se borra el token: puede ser un problema pasajero.
        if (activo && error.status !== 0) cerrarLocal();
      })
      .finally(() => activo && setCargando(false));
    return () => {
      activo = false;
    };
  }, [cerrarLocal]);

  const login = useCallback(async (email, password) => {
    const datos = await apiFetch("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(datos.token);
    setSalioAPropósito(false);
    setUsuario(datos.usuario);
    return datos.usuario;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/api/auth/logout/", { method: "POST" });
    } catch {
      /* aunque falle el aviso al servidor, se cierra la sesión acá */
    }
    setSalioAPropósito(true);
    cerrarLocal();
  }, [cerrarLocal]);

  const valor = useMemo(
    () => ({ usuario, cargando, salioAPropósito, login, logout }),
    [usuario, cargando, salioAPropósito, login, logout]
  );
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const contexto = useContext(AuthContext);
  if (!contexto) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return contexto;
}
