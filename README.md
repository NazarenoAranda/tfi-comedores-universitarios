# Sistema de Gestión de Caja y Proveedores — Comedores Universitarios

**Trabajo Final Integrador — Tecnicatura Universitaria en Programación (UTN)**

**Integrantes:** Nazareno Aranda, Julian Blanco Cortes
**Tipo de proyecto:** Inventiva propia (caso simulado)

Sistema web para una cadena de comedores universitarios que centraliza el registro de ventas, el cierre de caja de cada sede y el seguimiento de los pedidos a proveedores, y le da a la administración una vista consolidada de todas las sedes. Reemplaza el manejo actual con planillas de Excel y papel.

## Links

| | |
|---|---|
| **Aplicación en línea** | https://tfi-comedores-universitarios.vercel.app |
| **API (backend)** | https://tfi-comedores-api.onrender.com · [estado del servicio](https://tfi-comedores-api.onrender.com/api/health/) |
| **Video de presentación** | https://youtu.be/QZVu9Qq_rWA |
| **Informe final** | [`docs/05-Informe-Final.md`](docs/05-Informe-Final.md) |

> **Importante al probar la aplicación en línea:** el backend está en un plan gratuito que se "duerme" tras un rato sin uso. La **primera carga puede tardar hasta un minuto**; después funciona con normalidad.

### Usuarios de ejemplo (solo para pruebas)

La contraseña de todos es `Demo-1234`.

| Rol | Email | Qué puede hacer |
|---|---|---|
| Administración | `admin@comedores.test` | Todo: sedes, proveedores, cajas, ventas, pedidos y panel consolidado |
| Cajero | `cajero.ciencias@comedores.test` | Abrir y cerrar la caja de su sede y registrar ventas |
| Compras | `compras@comedores.test` | Proveedores y pedidos |

Hay además cajeros en las otras sedes (`cajero.central@comedores.test` y `cajero.norte@comedores.test`). Un recorrido sugerido: ingresar como cajero → abrir caja → cargar una venta → cerrar caja → ingresar como compras → registrar un pedido → ingresar como administración → ver el panel. El [manual de uso](docs/06-Manual-de-Uso.md) lo explica con capturas.

## Qué hace el sistema

| Módulo | Qué hace |
|---|---|
| **Usuarios y autenticación** | Ingreso con email y contraseña, token de sesión y tres roles: administración, cajero y compras |
| **Sedes** | Alta, modificación y baja de los comedores |
| **Proveedores** | Alta, modificación y baja de proveedores |
| **Caja** | Apertura y cierre de caja por sede, con totales por medio de pago y efectivo esperado |
| **Ventas** | Comprobantes con o sin detalle de productos, siempre dentro de una caja abierta; filtros por sede, fecha y medio de pago |
| **Pedidos** | Pedidos a proveedores con productos y estados (pendiente, recibido, cancelado) |
| **Panel consolidado** | Totales de ventas y pedidos de todas las sedes y por sede, con filtros de fechas |

Reglas que garantiza el sistema: una sola caja abierta por sede, no se vende con la caja cerrada, cada cajero solo ve su sede, nada se borra (las bajas son lógicas) y los importes no pierden precisión.

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 · Django 5.2 · Django REST Framework 3.16 |
| Autenticación | Token Authentication de DRF |
| Base de datos | PostgreSQL (Supabase) |
| Frontend | React 18 · Vite 7 · react-router-dom 7 |
| Despliegue | Backend en Render · base de datos en Supabase · frontend en Vercel |
| Pruebas | 54 pruebas automáticas del backend |
| Control de versiones | Git + GitHub (repositorio único) |

Arquitectura: **monolito modular en capas** (7 apps de Django, una por módulo) con una API REST que consume una aplicación React. Los detalles y la justificación de cada decisión están en [`docs/03-Arquitectura.md`](docs/03-Arquitectura.md).

## Estructura del repositorio

```
/backend      API Django + DRF (una app por módulo)
/frontend     Aplicación React + Vite
/database     schema.sql (estructura real), datos de ejemplo y script de limpieza
/docs         Documentación del proyecto
README.md     Este archivo
```

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/01-Propuesta.md`](docs/01-Propuesta.md) | Propuesta del proyecto: problemática, alcance, stack y plan de trabajo |
| [`docs/02-Diseno-BD-Modulos.md`](docs/02-Diseno-BD-Modulos.md) | Diseño de la base de datos, módulos y diferencias con el diseño original |
| [`docs/03-Arquitectura.md`](docs/03-Arquitectura.md) | Arquitectura, capas, tecnologías y justificación |
| [`docs/04-Despliegue.md`](docs/04-Despliegue.md) | Guía de despliegue en Supabase, Render y Vercel |
| [`docs/05-Informe-Final.md`](docs/05-Informe-Final.md) | Informe final: problema, solución, resultados, dificultades y aprendizajes |
| [`docs/06-Manual-de-Uso.md`](docs/06-Manual-de-Uso.md) | Manual de uso con capturas de pantalla |
| [`docs/07-Guion-Video.md`](docs/07-Guion-Video.md) | Guion del video de presentación |
| [`database/README.md`](database/README.md) | Base de datos y datos de ejemplo |
| [`backend/README.md`](backend/README.md) | API: instalación, endpoints y pruebas |
| [`frontend/README.md`](frontend/README.md) | Frontend: instalación y pantallas |

## Instalación y ejecución en local

**Requisitos:** Git, Python 3.10 o superior (se probó con 3.13) y Node.js 20.19 o superior (o 22.12 o superior) con npm. PostgreSQL es opcional: si no se configura, el backend usa SQLite.

### 1. Clonar el repositorio

```
git clone https://github.com/NazarenoAranda/tfi-comedores-universitarios.git
cd tfi-comedores-universitarios
```

### 2. Variables de entorno

Copiar `.env.example` como `.env` **en la raíz del repositorio** (el `.env` nunca se sube a GitHub):

```
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Con los valores por defecto el backend funciona en local con SQLite. Para usar PostgreSQL (por ejemplo, Supabase), completar `DATABASE_URL` (ver [`docs/04-Despliegue.md`](docs/04-Despliegue.md)).

### 3. Backend

Desde la carpeta `backend/`:

**Windows**

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**macOS / Linux**

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

El backend queda en http://localhost:8000. Para comprobarlo: http://localhost:8000/api/health/ debe responder `{"status":"ok","database":"ok"}`. El panel de administración (para crear sedes, usuarios, etc.) está en http://localhost:8000/admin/ y se ingresa con el superusuario recién creado. Si PowerShell no deja ejecutar `activate`, usar CMD o correr antes `Set-ExecutionPolicy -Scope Process Bypass`.

### 4. Frontend

En **otra terminal**, desde la carpeta `frontend/`:

```
cd frontend
npm install
npm run dev
```

La aplicación queda en http://localhost:5173 y usa el backend de http://localhost:8000 (variable `VITE_API_URL` del `.env`).

### 5. Datos de ejemplo (opcional)

El script `database/datos_ejemplo.sql` carga sedes, usuarios, proveedores, ventas y pedidos de ejemplo, pensado para **PostgreSQL**. Las instrucciones están en [`database/README.md`](database/README.md). Con SQLite, las sedes y los usuarios se crean desde `/admin/`.

### 6. Pruebas automáticas

Desde `backend/`, con el entorno virtual activado y `DATABASE_URL` vacío:

```
python manage.py test
```

Tiene que terminar con `Ran 54 tests` y `OK`. No tocan los datos reales.

## Despliegue

El sistema está publicado en tres servicios gratuitos: la base de datos en **Supabase**, el backend en **Render** y el frontend en **Vercel**; se actualizan solos con cada cambio en la rama `main`. El paso a paso está en [`docs/04-Despliegue.md`](docs/04-Despliegue.md).

## Estado del proyecto

| Etapa | Estado |
|---|---|
| 1. Propuesta y repositorio | Entregada |
| 2. Diseño de base de datos, módulos y arquitectura | Entregada |
| 3. Desarrollo, despliegue, informe y video | **Completa** (7 módulos implementados, probados y publicados) |

**Funcionalidades opcionales:** permisos por rol (hecho) y reportes comparativos entre sedes (parcial, en el panel). Quedaron como trabajo futuro: exportación del cierre de caja a PDF/Excel y alertas de pedidos demorados (ver el [informe final](docs/05-Informe-Final.md)).

## Integrantes

- Nazareno Aranda
- Julian Blanco Cortes
