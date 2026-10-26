// Cliente HTTP para hablar con el backend (Django REST Framework).
// La URL base sale de la variable de entorno VITE_API_URL (ver .env.example).

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");
const TOKEN_KEY = "token";

// El token de autenticación se guarda en el navegador. Se envuelve en try/catch
// porque el almacenamiento puede no estar disponible (modo privado, etc.).
export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* sin almacenamiento: la sesión dura solo mientras la pestaña esté abierta */
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* nada que limpiar */
  }
}

// Función que se llama cuando el servidor rechaza el token (sesión vencida o dada de baja).
let alSesionInvalida = null;
export function setUnauthorizedHandler(fn) {
  alSesionInvalida = fn;
}

// Llama a la API. Agrega el header "Authorization: Token <token>" si hay sesión.
// Si la respuesta no es exitosa lanza un Error con .status y .data (JSON del backend).
// Si no hay conexión con el servidor, el error tiene .status = 0.
export async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers });
  } catch {
    const error = new Error("Sin conexión con el servidor");
    error.status = 0;
    error.data = null;
    throw error;
  }

  if (!response.ok) {
    const error = new Error(`Error ${response.status} al llamar a ${path}`);
    error.status = response.status;
    try {
      error.data = await response.json();
    } catch {
      error.data = null;
    }
    if (response.status === 401 && token && alSesionInvalida) {
      alSesionInvalida();
    }
    throw error;
  }

  return response.status === 204 ? null : response.json();
}

// Arma "?a=1&b=2" ignorando los valores vacíos.
export function querystring(params = {}) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([clave, valor]) => {
    if (valor !== undefined && valor !== null && valor !== "") usp.set(clave, valor);
  });
  const texto = usp.toString();
  return texto ? `?${texto}` : "";
}

export { API_URL };
