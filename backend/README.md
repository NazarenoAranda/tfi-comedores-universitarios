# Backend

API REST del sistema, desarrollada con **Python + Django + Django REST Framework**, con autenticación por token (`Authorization: Token <token>`).

Estructura prevista: una app de Django por módulo (`usuarios`, `sedes`, `proveedores`, `caja`, `ventas`, `pedidos`, `dashboard`). Detalle en [`../docs/03-Arquitectura.md`](../docs/03-Arquitectura.md).

## Estado

| Módulo | Estado |
|---|---|
| Configuración base (Django, DRF, token, CORS, base de datos por variable de entorno) | Listo |
| `usuarios` — modelo de usuario con email y rol | Base lista (login y API en desarrollo) |
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

Todos los endpoints (salvo `health`) requieren el header `Authorization: Token <token>`.

| Método y dirección | Qué hace |
|---|---|
| `GET /api/health/` | Estado de la API y de la base (público) |
| `GET /api/sedes/` | Listado de sedes. Filtros: `?activa=true` o `?activa=false`, `?search=texto` |
| `POST /api/sedes/` | Alta de una sede |
| `GET /api/sedes/<id>/` | Detalle de una sede |
| `PUT` / `PATCH /api/sedes/<id>/` | Modificación de una sede |
| `DELETE /api/sedes/<id>/` | Baja lógica: la sede queda inactiva y no se borra, para conservar el historial |

Los listados están paginados de a 20 elementos (`count`, `next`, `previous`, `results`).

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
