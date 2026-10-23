# Backend

API REST del sistema, desarrollada con **Python + Django + Django REST Framework**, con autenticación por token (`Authorization: Token <token>`).

Estructura prevista: una app de Django por módulo (`usuarios`, `sedes`, `proveedores`, `caja`, `ventas`, `pedidos`, `dashboard`). Detalle en [`../docs/03-Arquitectura.md`](../docs/03-Arquitectura.md).

## Estado

| Módulo | Estado |
|---|---|
| Configuración base (Django, DRF, token, CORS, base de datos por variable de entorno) | Listo |
| `usuarios` — usuarios con rol y sede, login por token, permisos por rol | Listo |
| `sedes` — ABM de comedores | Listo |
| `proveedores` — ABM de proveedores | Listo |
| `caja` — apertura y cierre de caja con totales | Listo |
| `ventas` — comprobantes de venta con ítems y filtros | Listo |
| Resto de los módulos | Pendiente |

## Requisitos

- Python 3.10 o superior
- (Opcional) PostgreSQL. Si no se configura, se usa SQLite local.

## Puesta en marcha en local

Desde la carpeta `backend/`:

**Windows (CMD o PowerShell)**

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example ..\.env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**macOS / Linux**

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Notas:

- Si PowerShell no deja ejecutar `activate`, usar CMD o correr antes `Set-ExecutionPolicy -Scope Process Bypass`.
- El archivo `.env` va en la **raíz del repositorio** (no se sube a GitHub). Con los valores de `.env.example` el backend funciona en local con SQLite.
- `createsuperuser` pide email, nombre y contraseña: con ese usuario se ingresa al panel de administración.

Una vez levantado el servidor:

| Dirección | Qué es |
|---|---|
| http://localhost:8000/api/health/ | Chequeo de estado de la API y de la base de datos (público) |
| http://localhost:8000/admin/ | Panel de administración de Django |

## API disponible

Todos los endpoints, salvo `health` y `auth/login`, requieren el header `Authorization: Token <token>`. El token se obtiene con el login.

### Autenticación

| Método y dirección | Qué hace |
|---|---|
| `POST /api/auth/login/` | Recibe `email` y `password`. Devuelve `{"token": "...", "usuario": {...}}` |
| `POST /api/auth/logout/` | Invalida el token con el que se hizo el pedido |
| `GET /api/auth/me/` | Datos del usuario que inició sesión (id, nombre, email, rol, sede) |

Ejemplo de login:

```
POST /api/auth/login/
{"email": "caja@ejemplo.com", "password": "..."}

200 OK
{"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b", "usuario": {"id": 2, "nombre": "Cajera", "email": "caja@ejemplo.com", "rol": "cajero", "sede": 1, "sede_nombre": "Comedor Central", "is_active": true}}
```

Con credenciales incorrectas (o usuario dado de baja) responde `400` con el mismo mensaje en todos los casos, para no revelar si el email existe.

### Usuarios (solo administración)

| Método y dirección | Qué hace |
|---|---|
| `GET /api/usuarios/` | Listado. Filtros: `?rol=`, `?sede=<id>`, `?activo=true\|false`, `?search=texto` |
| `POST /api/usuarios/` | Alta (`nombre`, `email`, `password`, `rol`, `sede`) |
| `GET /api/usuarios/<id>/` | Detalle |
| `PUT` / `PATCH /api/usuarios/<id>/` | Modificación. La contraseña es opcional |
| `DELETE /api/usuarios/<id>/` | Baja lógica: queda inactivo, no se borra, y se cierran sus sesiones |

Reglas: el email es único (sin distinguir mayúsculas), la contraseña pasa las validaciones de Django, un **cajero debe tener sede**, y un administrador no puede darse de baja a sí mismo. Al cambiar la contraseña de un usuario se cierran sus sesiones abiertas.

### Sedes

| Método y dirección | Qué hace |
|---|---|
| `GET /api/sedes/` | Listado de sedes. Filtros: `?activa=true` o `?activa=false`, `?search=texto` |
| `POST /api/sedes/` | Alta de una sede |
| `GET /api/sedes/<id>/` | Detalle de una sede |
| `PUT` / `PATCH /api/sedes/<id>/` | Modificación de una sede |
| `DELETE /api/sedes/<id>/` | Baja lógica: la sede queda inactiva y no se borra, para conservar el historial |

### Proveedores (administración y compras)

| Método y dirección | Qué hace |
|---|---|
| `GET /api/proveedores/` | Listado. Filtros: `?activo=true` o `?activo=false`, `?search=texto` (nombre, contacto, email o teléfono) |
| `POST /api/proveedores/` | Alta (`nombre` obligatorio; `contacto`, `telefono` y `email` opcionales) |
| `GET /api/proveedores/<id>/` | Detalle |
| `PUT` / `PATCH /api/proveedores/<id>/` | Modificación |
| `DELETE /api/proveedores/<id>/` | Baja lógica: el proveedor queda inactivo y no se borra, para conservar el historial de pedidos |

### Caja (administración y cajeros)

Un cajero solo ve y opera las cajas de su sede; la administración ve todas. Las cajas no se modifican ni se borran por la API.

| Método y dirección | Qué hace |
|---|---|
| `POST /api/cajas/` | Apertura. Cuerpo: `{"monto_apertura": 5000}` (opcional, por defecto 0). La administración debe indicar además `"sede": <id>` |
| `GET /api/cajas/` | Listado. Filtros: `?sede=`, `?estado=abierta\|cerrada`, `?usuario=`, `?desde=AAAA-MM-DD`, `?hasta=AAAA-MM-DD` |
| `GET /api/cajas/<id>/` | Detalle, con el resumen de ventas (`totales`) |
| `GET /api/cajas/actual/` | Caja abierta de la sede del cajero (la administración indica `?sede=<id>`). `404` si no hay ninguna |
| `GET /api/cajas/<id>/totales/` | Resumen de ventas de la caja |
| `POST /api/cajas/<id>/cerrar/` | Cierre: calcula los totales, guarda `monto_cierre_calculado` y deja la caja cerrada |

Reglas: cada sede puede tener **una sola caja abierta** a la vez (lo garantiza también la base de datos), no se abre caja en una sede dada de baja, y una caja cerrada no se puede volver a cerrar.

Resumen de ventas (`totales`):

```
{
  "cantidad_comprobantes": 6,
  "total_ventas": "6450.75",
  "por_medio_pago": {
    "efectivo":      {"cantidad": 2, "total": "2000.50"},
    "tarjeta":       {"cantidad": 2, "total": "3000.01"},
    "transferencia": {"cantidad": 1, "total": "999.99"},
    "qr":            {"cantidad": 1, "total": "450.25"}
  },
  "monto_apertura": "5000.50",
  "efectivo_esperado": "7001.00"
}
```

`efectivo_esperado` = monto de apertura + ventas cobradas en efectivo: es lo que debería haber en la caja física al cerrar. Las ventas con tarjeta, transferencia o QR no pasan por la caja. Los importes viajan como texto para no perder precisión.

Los totales se calculan a partir de los comprobantes de venta cargados en esa caja (módulo de ventas).

### Ventas / Comprobantes (administración y cajeros)

Un cajero carga las ventas en la **caja abierta de su sede** y solo ve los comprobantes de su sede; la administración ve todos y debe indicar la caja al cargar. Los comprobantes **no se modifican ni se borran** por la API: son el respaldo del cierre de caja.

| Método y dirección | Qué hace |
|---|---|
| `POST /api/comprobantes/` | Alta de una venta (ver abajo) |
| `GET /api/comprobantes/` | Listado, del más nuevo al más viejo. Filtros: `?sede=`, `?caja=`, `?usuario=`, `?medio_pago=efectivo\|tarjeta\|transferencia\|qr`, `?desde=AAAA-MM-DD`, `?hasta=AAAA-MM-DD` (ambas fechas inclusivas) |
| `GET /api/comprobantes/<id>/` | Detalle, con sus ítems |

Se puede cargar de dos formas:

```
POST /api/comprobantes/
{"medio_pago": "efectivo",
 "items": [{"descripcion": "Menú del día", "cantidad": 2, "precio_unitario": "1500.50"},
           {"descripcion": "Agua", "cantidad": 1, "precio_unitario": "800"}]}

201 Created
{"id": 7, "caja": 3, "sede": 1, "sede_nombre": "Comedor Central", "usuario": 2, "usuario_nombre": "Cajera",
 "fecha": "2026-10-22T13:05:00Z", "medio_pago": "efectivo", "monto_total": "3801.00",
 "items": [{"id": 1, "descripcion": "Menú del día", "cantidad": 2, "precio_unitario": "1500.50", "subtotal": "3001.00"}, ...]}
```

o solo con el monto total, sin ítems: `{"medio_pago": "qr", "monto_total": "1500"}`.

Reglas: **solo se cargan ventas con la caja abierta** (si no hay una abierta en la sede, o está cerrada, responde `400`); con ítems, el monto total se calcula como la suma de cantidad × precio (si se envía y no coincide, `400`); el monto debe ser mayor a cero; la sede, el usuario y la fecha los pone el sistema. La caja se bloquea al guardar la venta, así que una venta no puede "colarse" mientras se está cerrando la caja.

### Estado del sistema

| Método y dirección | Qué hace |
|---|---|
| `GET /api/health/` | Estado de la API y de la base (público) |

Los listados están paginados de a 20 elementos (`count`, `next`, `previous`, `results`).

## Permisos por rol

| Recurso | Administración | Cajero | Compras |
|---|---|---|---|
| Usuarios | Todo | — | — |
| Sedes | Todo | Solo consulta | Solo consulta |
| Proveedores | Todo | — | Todo |
| Caja | Todo | Solo su sede | — |
| Comprobantes (ventas) | Todo | Solo su sede | — |

Los permisos de los módulos siguientes (pedidos, dashboard) se suman a esta tabla a medida que se desarrollan. Las reglas están en `usuarios/permissions.py`.

## Primer uso: crear usuarios

1. Crear el administrador con `python manage.py createsuperuser` (queda con rol `admin`).
2. Ingresar a http://localhost:8000/admin/ y crear las sedes y los demás usuarios (o hacerlo por la API con el token del administrador).

## Configuración por variables de entorno

Todo lo que cambia entre desarrollo y producción se lee de variables de entorno (ver `../.env.example`):

| Variable | Para qué sirve |
|---|---|
| `DEBUG` | `True` solo en desarrollo. En producción debe ser `False`. |
| `SECRET_KEY` | Clave secreta de Django (obligatoria si `DEBUG` es `False`). |
| `ALLOWED_HOSTS` | Hosts permitidos, separados por coma. |
| `CORS_ALLOWED_ORIGINS` | Orígenes del frontend autorizados a usar la API. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes de confianza para el panel de administración en producción. |
| `DATABASE_URL` | URL de PostgreSQL (por ejemplo Supabase). Vacía = SQLite local. |

## Decisiones de esta etapa

- **Modelo de usuario propio** desde el inicio: Django obliga a definirlo antes de la primera migración. El usuario inicia sesión con su email y tiene un rol (`admin`, `cajero` o `compras`).
- **Nombres de tablas** alineados con `database/schema.sql` (por ejemplo `usuario`).
- **Paginación** de 20 elementos por página en los listados de la API.
- **WhiteNoise** sirve los archivos estáticos del panel de administración en producción.
