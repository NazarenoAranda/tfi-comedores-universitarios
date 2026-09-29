-- ============================================================
-- Sistema de gestión de caja y proveedores — Comedores Universitarios
-- Script DDL — PostgreSQL
-- ============================================================

CREATE TABLE sede (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    universidad VARCHAR(150),
    direccion VARCHAR(200),
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE usuario (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'cajero', 'compras')),
    sede_id BIGINT REFERENCES sede(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE caja (
    id BIGSERIAL PRIMARY KEY,
    sede_id BIGINT NOT NULL REFERENCES sede(id),
    usuario_id BIGINT NOT NULL REFERENCES usuario(id),
    fecha_apertura TIMESTAMP NOT NULL DEFAULT now(),
    fecha_cierre TIMESTAMP,
    monto_apertura NUMERIC(12,2) NOT NULL DEFAULT 0,
    monto_cierre_calculado NUMERIC(12,2),
    estado VARCHAR(20) NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada'))
);

CREATE TABLE comprobante (
    id BIGSERIAL PRIMARY KEY,
    caja_id BIGINT NOT NULL REFERENCES caja(id),
    sede_id BIGINT NOT NULL REFERENCES sede(id),
    usuario_id BIGINT NOT NULL REFERENCES usuario(id),
    fecha TIMESTAMP NOT NULL DEFAULT now(),
    medio_pago VARCHAR(20) NOT NULL CHECK (medio_pago IN ('efectivo', 'tarjeta', 'transferencia', 'qr')),
    monto_total NUMERIC(12,2) NOT NULL
);

CREATE TABLE item_comprobante (
    id BIGSERIAL PRIMARY KEY,
    comprobante_id BIGINT NOT NULL REFERENCES comprobante(id) ON DELETE CASCADE,
    descripcion VARCHAR(150) NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(12,2) NOT NULL
);

CREATE TABLE proveedor (
    id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    contacto VARCHAR(150),
    telefono VARCHAR(50),
    email VARCHAR(150),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pedido (
    id BIGSERIAL PRIMARY KEY,
    proveedor_id BIGINT NOT NULL REFERENCES proveedor(id),
    sede_id BIGINT NOT NULL REFERENCES sede(id),
    usuario_id BIGINT NOT NULL REFERENCES usuario(id),
    fecha_pedido TIMESTAMP NOT NULL DEFAULT now(),
    fecha_recibido TIMESTAMP,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'recibido', 'cancelado')),
    monto_total NUMERIC(12,2)
);

CREATE TABLE item_pedido (
    id BIGSERIAL PRIMARY KEY,
    pedido_id BIGINT NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    descripcion VARCHAR(150) NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(12,2) NOT NULL
);

-- ============================================================
-- Índices recomendados
-- ============================================================
CREATE INDEX idx_usuario_sede ON usuario(sede_id);
CREATE INDEX idx_caja_sede ON caja(sede_id);
CREATE INDEX idx_comprobante_caja ON comprobante(caja_id);
CREATE INDEX idx_comprobante_sede_fecha ON comprobante(sede_id, fecha);
CREATE INDEX idx_pedido_proveedor ON pedido(proveedor_id);
CREATE INDEX idx_pedido_sede_estado ON pedido(sede_id, estado);
