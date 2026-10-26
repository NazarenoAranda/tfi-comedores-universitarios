# Base de datos

Motor: **PostgreSQL** (alojada en Supabase).

| Archivo | Contenido |
|---|---|
| [`schema.sql`](schema.sql) | Script DDL: crea las 8 tablas del sistema y sus índices (diseño original) |
| [`datos_ejemplo.sql`](datos_ejemplo.sql) | Script DML: datos de ejemplo para probar y demostrar el sistema |
| [`limpiar_datos_ejemplo.sql`](limpiar_datos_ejemplo.sql) | Borra los datos de ejemplo para poder volver a cargarlos |

El diagrama entidad-relación, el diccionario de datos y la explicación de cada índice están en [`../docs/02-Diseno-BD-Modulos.md`](../docs/02-Diseno-BD-Modulos.md).

## Cómo se crean las tablas

Las tablas reales las crea Django con `python manage.py migrate` (ver [`../backend/README.md`](../backend/README.md)); usan los mismos nombres que `schema.sql`. Los datos de ejemplo se cargan **después** de las migraciones.

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
