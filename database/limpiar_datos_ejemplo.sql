-- ============================================================================
-- Borra los datos de ejemplo (y todo lo que se haya cargado encima) para poder volver a
-- ejecutar datos_ejemplo.sql.
--
-- ATENCIÓN: borra TODOS los comprobantes, cajas, pedidos, proveedores y sedes, y los
-- usuarios @comedores.test. NO borra el superusuario ni otros usuarios. Si algún usuario
-- que no sea de ejemplo está asignado a una sede, la última sentencia falla y no se borra
-- nada (hay que cambiarle la sede desde el panel de administración).
-- No usar en la base con datos reales.
-- ============================================================================

BEGIN;

DELETE FROM item_comprobante;
DELETE FROM comprobante;
DELETE FROM caja;
DELETE FROM item_pedido;
DELETE FROM pedido;
DELETE FROM proveedor;

DELETE FROM authtoken_token WHERE user_id IN (SELECT id FROM usuario WHERE email LIKE '%@comedores.test');
DELETE FROM django_admin_log WHERE user_id IN (SELECT id FROM usuario WHERE email LIKE '%@comedores.test');
DELETE FROM usuario WHERE email LIKE '%@comedores.test';

DELETE FROM sede;

COMMIT;
