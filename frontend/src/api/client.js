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

// Llama a la API. Agrega el header "Authorization: Token <token>" si hay sesión.
// Si la respuesta no es exitosa lanza un Error con .status y .data (JSON del backend).
export async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    const error = new Error(`Error ${response.status} al llamar a ${path}`);
    error.status = response.status;
    try {
      error.data = await response.json();
    } catch {
      error.data = null;
    }
    throw error;
  }

  return response.status === 204 ? null : response.json();
}

export { API_URL };
