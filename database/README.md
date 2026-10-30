# Base de datos

Motor: **PostgreSQL** (alojada en Supabase).

| Archivo | Contenido |
|---|---|
| [`schema.sql`](schema.sql) | Script DDL con la estructura **real** de las 8 tablas del sistema, sus restricciones e índices |
| [`datos_ejemplo.sql`](datos_ejemplo.sql) | Script DML: datos de ejemplo para probar y demostrar el sistema |
| [`limpiar_datos_ejemplo.sql`](limpiar_datos_ejemplo.sql) | Borra los datos de ejemplo para poder volver a cargarlos |

El diagrama entidad-relación, el diccionario de datos y la explicación de cada índice están en [`../docs/02-Diseno-BD-Modulos.md`](../docs/02-Diseno-BD-Modulos.md).

## Cómo se crean las tablas

Las tablas reales las crea Django con `python manage.py migrate` (ver [`../backend/README.md`](../backend/README.md)). `schema.sql` es su descripción en SQL: tiene la misma estructura (se verificó cargándolo en una base vacía y comparando columnas, tipos, restricciones e índices con la base que crea `migrate`) y sirve para leerla de una vez o, si hiciera falta, crearla a mano en una base vacía. **En el uso normal no se ejecuta.**

El script ya no es el diseño original: se actualizó con lo realmente construido. Las diferencias (contraseña con formato de Django, fechas con zona horaria, restricciones nuevas, una sola caja abierta por sede, etc.) están en el encabezado del propio archivo y explicadas en la sección 1.7 de [`../docs/02-Diseno-BD-Modulos.md`](../docs/02-Diseno-BD-Modulos.md).

`migrate` agrega además tablas internas de Django y de la autenticación por token (`authtoken_token`, `auth_*`, `django_*`, `usuario_groups`…); no tienen datos del negocio y no figuran en `schema.sql`. Los datos de ejemplo se cargan **después** de crear las tablas.

## Datos de ejemplo

`datos_ejemplo.sql` carga:

| Qué | Cantidad |
|---|---|
| Sedes | 3 activas y 1 dada de baja |
| Usuarios | 5 (administración, compras y un cajero por sede) |
| Proveedores | 6 (1 dado de baja) |
| Cajas | 18 cerradas (los últimos 6 días, en las 3 sedes) y 2 abiertas hoy (sedes Central y Campus Norte) |
| Comprobantes de venta | 303, con sus ítems, en los cuatro medios de pago |
| Pedidos | 14 en los tres estados, con ítems |

Las fechas son relativas al día en que se ejecuta. La sede **Comedor Ciencias** queda sin caja abierta a propósito, para poder probar la apertura de caja.

**Usuarios de ejemplo** (la contraseña de todos es `Demo-1234`; solo para pruebas, no usar en un sistema real):

| Rol | Email | Sede |
|---|---|---|
| Administración | `admin@comedores.test` | — |
| Compras | `compras@comedores.test` | — |
| Cajero | `cajero.central@comedores.test` | Comedor Central |
| Cajero | `cajero.norte@comedores.test` | Comedor Campus Norte |
| Cajero | `cajero.ciencias@comedores.test` | Comedor Ciencias |

### Cómo cargarlos

**Opción A — Supabase (SQL Editor):** en el panel del proyecto, **SQL Editor → New query**, pegar el contenido de `datos_ejemplo.sql` y **Run**.

**Opción B — con `psql`**, usando la misma cadena del *Session pooler* que `DATABASE_URL`:

```
psql "postgresql://postgres.<ref>:<CONTRASEÑA>@aws-N-<región>.pooler.supabase.com:5432/postgres?sslmode=require" -f database/datos_ejemplo.sql
```

El script se ejecuta en una sola transacción: si algo falla, no queda nada a medias. **Se ejecuta una sola vez**: si la base ya tiene sedes, proveedores, cajas, comprobantes o pedidos, se detiene con un mensaje y no cambia nada. Para borrar todo y volver a cargar, ejecutar primero `limpiar_datos_ejemplo.sql` (borra *todas* las sedes, cajas, comprobantes, pedidos y proveedores, y los usuarios `@comedores.test`; no toca al superusuario).
