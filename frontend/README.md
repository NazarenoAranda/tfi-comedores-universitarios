# Frontend

Aplicación web del sistema, desarrollada con **React + Vite**. Consume la API REST del backend (autenticación por token) y se despliega en Vercel.

## Estado

| Pantalla | Estado |
|---|---|
| Inicio de sesión (login con token), rutas protegidas por rol, menú y diseño general | Listo |
| Sedes y proveedores (listado, búsqueda, alta, modificación y baja) | Listo |
| Caja (apertura, cierre, totales e historial) y ventas (cargar y listar comprobantes) | Listo |
| Pedidos a proveedores (alta, listado con filtros, recibir y cancelar) | Listo |
| Panel consolidado | Pendiente (30/10) |

## Requisitos

- Node.js 20.19 o superior (o 22.12 o superior) y npm.
- El backend levantado (ver [`../backend/README.md`](../backend/README.md)) y, para tener datos, los datos de ejemplo (ver [`../database/README.md`](../database/README.md)).

## Puesta en marcha en local

Desde la carpeta `frontend/`:

```
npm install
npm run dev
```

Se abre en http://localhost:5173. La dirección del backend sale de `VITE_API_URL` del archivo `.env` de la **raíz del repositorio** (copia de `.env.example`); por defecto, `http://localhost:8000`. Si cambiás ese archivo, reiniciá `npm run dev`.

Para ingresar hace falta un usuario: los de ejemplo (`admin@comedores.test`, `compras@comedores.test`, `cajero.central@comedores.test`, contraseña `Demo-1234`) o el superusuario creado en el backend.

Otros comandos: `npm run build` (genera la versión de producción en `dist/`) y `npm run preview` (la sirve en local).

## Cómo está organizado

```
src/
  api/        client.js (llamadas a la API con el token), errores.js (mensajes de error)
  auth/       AuthContext.jsx (sesión: login/logout), RutaProtegida.jsx (por rol)
  components/ Layout (encabezado y menú), Mensaje, Paginacion
  pages/      una pantalla por archivo
  utils/      formato.js (importes y fechas)
  menu.js     lista de pantallas y qué roles las ven
  App.jsx     rutas
```

- **Sesión:** al ingresar, el backend devuelve un token que se guarda en el navegador y se envía en cada llamada (`Authorization: Token <token>`). Si el servidor lo rechaza, la aplicación vuelve al login.
- **Roles:** el menú y las rutas dependen del rol (administración, cajero, compras). Es una comodidad de la interfaz: los permisos reales los controla siempre el backend.
