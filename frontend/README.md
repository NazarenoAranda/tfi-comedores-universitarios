# Frontend

Aplicación web del sistema, desarrollada con **React + Vite** y **React Router**. Consume la API REST del backend y se despliega en Vercel.

## Estado

| Parte | Estado |
|---|---|
| Proyecto base (Vite, React, router, estructura de carpetas) | Listo |
| Cliente de la API (URL por variable de entorno, header con token) | Listo |
| Login y rutas protegidas | Pendiente |
| Pantallas de los módulos | Pendiente |

## Requisitos

- Node.js 20.19 o superior (o 22.12 o superior) y npm.
- El backend levantado para ver la conexión (ver [`../backend/README.md`](../backend/README.md)).

## Puesta en marcha en local

Desde la carpeta `frontend/`:

```
npm install
npm run dev
```

La aplicación queda en http://localhost:5173. La pantalla de inicio muestra si se pudo conectar con el backend.

Otros comandos:

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo con recarga automática |
| `npm run build` | Genera la versión de producción en `dist/` |
| `npm run preview` | Sirve la versión de producción para probarla |

## Configuración

La URL del backend se toma de la variable **`VITE_API_URL`**. Vite la lee del archivo `.env` de la **raíz del repositorio** (copiar `../.env.example` como `.env`). En producción se define en el panel de Vercel.

Si no está definida, se usa `http://localhost:8000`.

## Estructura

```
src/
  api/          Cliente HTTP (URL base y token de autenticación)
  components/   Componentes reutilizables (Layout con el menú)
  pages/        Pantallas, una por ruta
  App.jsx       Definición de rutas
  main.jsx      Punto de entrada
  index.css     Estilos globales
```
