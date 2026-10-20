# Backend

API REST del sistema, desarrollada con **Python + Django + Django REST Framework**, con autenticación por token (`Authorization: Token <token>`).

Estructura prevista: una app de Django por módulo (`usuarios`, `sedes`, `proveedores`, `caja`, `ventas`, `pedidos`, `dashboard`). Detalle en [`../docs/03-Arquitectura.md`](../docs/03-Arquitectura.md).

## Estado

| Módulo | Estado |
|---|---|
| Configuración base (Django, DRF, token, CORS, base de datos por variable de entorno) | Listo |
| `usuarios` — usuarios con rol y sede, login por token, permisos por rol | Listo |
| `sedes` — ABM de comedores | Listo |
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

Los permisos de los módulos siguientes (proveedores, caja, ventas, pedidos) se suman a esta tabla a medida que se desarrollan. Las reglas están en `usuarios/permissions.py`.

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
