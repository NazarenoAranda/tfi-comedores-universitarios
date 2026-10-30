# Informe Final — Sistema de gestión de caja y proveedores

**Trabajo Final Integrador — Tecnicatura Universitaria en Programación (UTN)**
**Integrantes:** Nazareno Aranda, Julian Blanco Cortes
**Proyecto:** Sistema de gestión de caja y proveedores para una cadena de comedores universitarios (caso simulado, inventiva propia)

| | |
|---|---|
| **Repositorio** | https://github.com/NazarenoAranda/tfi-comedores-universitarios |
| **Aplicación en línea (frontend)** | `COMPLETAR-URL-DE-VERCEL` |
| **API en línea (backend)** | `COMPLETAR-URL-DE-RENDER`/api/health/ |
| **Video de presentación** | `COMPLETAR-LINK-DEL-VIDEO` |

> *Versión en elaboración: este commit incluye la primera parte; la segunda (7 a 11) se agrega en el siguiente.*
>
> **Índice.** Primera parte: 1. Problema · 2. Solución · 3. Arquitectura · 4. Módulos · 5. Tecnologías · 6. Despliegue.
> Segunda parte: 7. Resultados · 8. Dificultades · 9. Aprendizajes · 10. Trabajo futuro · 11. Conclusión.

---

# Primera parte

## 1. El problema

### 1.1 Contexto

Se plantea el caso de una **cadena de comedores universitarios**: una administración central que gestiona varios comedores (sedes) dentro del ámbito de una o más universidades. Cada sede tiene un encargado de caja que registra las ventas del día; además, un encargado de compras gestiona los pedidos a los proveedores (insumos, alimentos, bebidas).

| Actor | Qué hace | Qué necesita |
|---|---|---|
| Administración (dueño) | Supervisa todas las sedes | Ver ventas y pedidos de todas las sedes juntos, sin esperar reportes manuales |
| Encargado de caja (por sede) | Registra las ventas del día | Cargar comprobantes rápido y cerrar la caja sin hacer cuentas a mano |
| Encargado de compras | Pide mercadería a los proveedores | Saber qué se pidió, a quién y en qué estado está cada pedido |

### 1.2 Situación de partida

Hoy la información se lleva con **planillas de Excel sueltas y anotaciones en papel**, sin un criterio común entre sedes. Cada comedor maneja sus datos de forma aislada.

### 1.3 Enunciado

> El personal de una cadena de comedores universitarios —encargados de caja en cada sede, encargado de compras y la administración central— registra las ventas diarias y los pedidos a proveedores con Excel y papel, sin un criterio centralizado entre sedes. Esto hace que armar el cierre de caja lleve mucho tiempo y que no haya forma rápida de consolidar la información de todas las sedes.

### 1.4 Por qué una solución de software

Una planilla, aunque esté bien armada, depende de la disciplina de cada persona en cada sede y no ofrece una vista central. Un sistema con una interfaz simple reduce el esfuerzo del registro diario, **calcula solo el cierre de caja** y **consolida automáticamente** los datos de todas las sedes.

### 1.5 Alcance

**Dentro del alcance (MVP):** comprobantes de venta por sede, cierre de caja con cálculo automático, proveedores, pedidos con seguimiento de estado, panel consolidado para la administración y permisos según el rol.

**Fuera del alcance:** facturación electrónica o integración con AFIP, control de stock, aplicación móvil nativa y pagos en línea. El sistema **registra** el medio de pago; no procesa cobros.

La propuesta original completa está en [`01-Propuesta.md`](./01-Propuesta.md).

## 2. La solución

Se construyó una **aplicación web** con tres partes: una interfaz que se usa desde el navegador (en la computadora o el celular), una API que concentra las reglas del negocio y una base de datos que guarda todo en un solo lugar. Cada persona entra con su correo y su contraseña y **ve solo lo que le corresponde según su rol**:

| Rol | Qué puede hacer en el sistema |
|---|---|
| **Administración** | Todo: gestiona sedes, usuarios (por el panel `/admin/` o la API) y proveedores; ve las cajas, ventas y pedidos de todas las sedes; consulta el panel consolidado. |
| **Cajero** | Abre y cierra la caja **de su sede** y registra ventas. Solo ve datos de su sede. |
| **Compras** | Gestiona proveedores y pedidos (cargar, marcar como recibido, cancelar). |

**El flujo de trabajo**, de punta a punta:

1. La administración da de alta las **sedes** y los **proveedores** desde la aplicación, y los **usuarios** desde el panel de administración (`/admin/`).
2. Al empezar el turno, el cajero **abre la caja** indicando el efectivo inicial.
3. Durante el día registra cada **venta** (comprobante) con su medio de pago, con o sin detalle de ítems; el sistema calcula el total.
4. Al terminar, el cajero **cierra la caja**: el sistema muestra el total por medio de pago y el efectivo que debería haber, sin cuentas manuales.
5. El encargado de compras carga **pedidos** a los proveedores y los marca como recibidos o cancelados.
6. La administración mira el **panel consolidado**: ventas y pedidos de cada sede y del total.

**Reglas del negocio que garantiza el sistema** (y que verifican las pruebas automáticas):

- Una sede no puede tener dos cajas abiertas a la vez, ni siquiera si dos cajeros intentan abrirla al mismo tiempo.
- No se puede registrar una venta si la caja está cerrada.
- Un cajero no puede ver ni modificar datos de otra sede.
- Una caja cerrada o un pedido ya recibido o cancelado no vuelven a cambiar.
- Nada se borra: las sedes, usuarios y proveedores se **dan de baja** (de forma lógica), para conservar el historial.
- Los importes se manejan sin errores de redondeo.

## 3. Arquitectura

La arquitectura es **cliente-servidor con una API REST**: el navegador carga una aplicación React que se comunica con una API (Django + Django REST Framework), y solo la API accede a la base de datos PostgreSQL.

```mermaid
flowchart LR
    U["Usuarios<br/>administración / cajero / compras"] --> F["Frontend<br/>React + Vite<br/>(Vercel)"]
    F -- "HTTPS + JSON<br/>Authorization: Token" --> B["Backend<br/>Django + DRF<br/>(Render)"]
    B -- "ORM de Django" --> D[("PostgreSQL<br/>(Supabase)")]
```

**Estilo: monolito modular en capas.** El backend es una única aplicación, dividida en siete apps de Django (una por módulo) y, dentro de cada una, en capas con una responsabilidad cada una:

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Rutas | `urls.py` | Qué dirección de la API atiende cada vista |
| Vistas | `views.py` | Verifica permisos y ejecuta la lógica de cada operación |
| Serializadores | `serializers.py` | Valida los datos que llegan y los convierte a JSON |
| Modelos | `models.py` | Entidades, relaciones y restricciones |
| Servicios | `services.py` | Cálculos reutilizables (totales de caja, consultas del panel) |

**Decisiones principales:** se eligió un monolito (y no microservicios) porque el sistema lo usarán pocas personas por sede y el equipo es de dos; Django, porque trae autenticación, ORM y panel de administración; PostgreSQL, porque los datos son estructurados y relacionales; y autenticación por token, porque frontend y backend viven en dominios distintos. Las alternativas descartadas y sus motivos están en [`03-Arquitectura.md`](./03-Arquitectura.md).

**Base de datos.** Son 8 tablas de negocio: `sede`, `usuario`, `caja`, `comprobante`, `item_comprobante`, `proveedor`, `pedido` e `item_pedido`. Parte de las reglas están también como restricciones de la base (un índice único parcial garantiza una sola caja abierta por sede; los montos deben ser positivos; las cantidades, al menos 1). El diagrama entidad-relación, el diccionario de datos y la lista de diferencias entre el diseño y lo construido están en [`02-Diseno-BD-Modulos.md`](./02-Diseno-BD-Modulos.md) y en [`../database/schema.sql`](../database/schema.sql).

## 4. Módulos

El sistema se organiza en siete módulos. Los siete están implementados, probados y desplegados.

| # | Módulo | Qué hace | Quién lo usa |
|---|---|---|---|
| 1 | **Usuarios y autenticación** | Ingreso con correo y contraseña, token de sesión, cierre de sesión y alta, modificación y baja de usuarios con rol | Todos (la gestión de usuarios, solo administración, por la API y el panel `/admin/`) |
| 2 | **Sedes** | Alta, modificación y baja de comedores | Administración (los demás roles consultan) |
| 3 | **Proveedores** | Alta, modificación y baja de proveedores | Administración y compras |
| 4 | **Caja** | Apertura y cierre de caja por sede; totales por medio de pago y efectivo esperado | Cajeros y administración |
| 5 | **Ventas / comprobantes** | Registro de ventas con o sin ítems, siempre dentro de una caja abierta; listado con filtros por sede, fecha y medio de pago | Cajeros y administración |
| 6 | **Pedidos** | Pedidos a proveedores con ítems y estados (pendiente, recibido, cancelado) | Compras y administración |
| 7 | **Panel consolidado** | Totales de ventas y pedidos de todas las sedes y por sede, con filtro de fechas | Administración |

**Interfaz.** El frontend tiene una pantalla por módulo: ingreso, inicio, sedes, proveedores, caja, ventas, pedidos y panel. El menú muestra solo las secciones permitidas para el rol, las rutas están protegidas, y la aplicación se adapta al celular. Las capturas de pantalla de cada paso están en el [Manual de uso](./06-Manual-de-Uso.md).

> **Sobre la seguridad.** La interfaz oculta las opciones que un rol no puede usar, pero eso es solo comodidad: **la seguridad la aplica siempre el backend**. Aunque alguien intentara llamar a la API directamente, un cajero no puede ver otra sede ni un encargado de compras puede cerrar una caja.

## 5. Tecnologías

| Capa | Tecnología | Por qué |
|---|---|---|
| Lenguaje del backend | Python 3.13 | Lo conoce el equipo |
| Framework | Django 5.2 + Django REST Framework 3.16 | ORM, validación, autenticación y panel de administración incluidos |
| Autenticación | Token Authentication de DRF | Simple y adecuada para un frontend en otro dominio |
| Base de datos | PostgreSQL en Supabase | Datos relacionales con integridad; la base gratuita de Render vence a los 30 días, menos que la duración del proyecto |
| Servidor de producción | gunicorn + whitenoise | Servidor WSGI estándar y archivos estáticos del panel de administración |
| Seguridad web | django-cors-headers, variables de entorno | Permite solo el dominio del frontend; las claves nunca van en el código |
| Frontend | React 18 + Vite 7 + react-router-dom 7 | Interfaz ágil para el uso diario y despliegue independiente |
| Pruebas | Ejecutor de pruebas de Django (54 pruebas) | Comprueban las reglas del negocio y los permisos |
| Hosting | Render (API), Supabase (base), Vercel (frontend) | Planes gratuitos y despliegue desde GitHub |
| Control de versiones | Git + GitHub | Repositorio único, con commits por funcionalidad |

## 6. Despliegue

El sistema está publicado en tres servicios gratuitos que se conectan entre sí y se actualizan solos con cada cambio en la rama `main` de GitHub:

```mermaid
flowchart LR
    G["GitHub<br/>rama main"] -- "despliegue automático" --> R["Render<br/>API (carpeta backend)"]
    G -- "despliegue automático" --> V["Vercel<br/>frontend (carpeta frontend)"]
    V -- "VITE_API_URL" --> R
    R -- "DATABASE_URL<br/>Session pooler + SSL" --> S[("Supabase<br/>PostgreSQL")]
```

| Servicio | Qué aloja | Puntos clave de la configuración |
|---|---|---|
| **Supabase** | La base PostgreSQL | Conexión por *Session pooler* con SSL (la conexión directa usa IPv6 y puede no ser alcanzable desde el hosting); *Data API* desactivada, porque Django se conecta directo a PostgreSQL y no hace falta exponer una API pública de la base |
| **Render** | La API Django | Directorio raíz `backend`; construcción con `bash build.sh` (instala dependencias, junta los estáticos y aplica las migraciones); arranque con `gunicorn`; verificación de estado en `/api/health/`; clave secreta, `DEBUG=False`, `DATABASE_URL` y orígenes permitidos como variables de entorno |
| **Vercel** | El frontend React | Directorio raíz `frontend`; variable `VITE_API_URL` apuntando a la API; `vercel.json` con la regla que hace que las rutas de la aplicación funcionen al recargar la página |

**Detalles que importan:**

- **CORS:** el backend solo acepta pedidos desde la dirección del frontend en Vercel, que se carga en `CORS_ALLOWED_ORIGINS`.
- **Variables de entorno:** `SECRET_KEY`, `DATABASE_URL` y demás valores sensibles viven en el panel de cada servicio y en un archivo `.env` local que **no se sube** al repositorio.
- **Plan gratuito de Render:** el servicio se "duerme" tras un rato sin uso y el primer pedido puede tardar cerca de un minuto en responder; después anda con normalidad.
- **Primer usuario:** el administrador inicial se crea con un comando (`createsuperuser`); a partir de ahí, los demás usuarios se crean desde el panel de administración de Django (`/admin/`) o desde la API (`/api/usuarios/`); la interfaz React no incluye una pantalla de usuarios. Para demostraciones se puede cargar `database/datos_ejemplo.sql`.

La guía paso a paso (con todas las variables y la lista de verificación) está en [`04-Despliegue.md`](./04-Despliegue.md).

---

*Continúa en la segunda parte: resultados, dificultades, aprendizajes y trabajo futuro.*
