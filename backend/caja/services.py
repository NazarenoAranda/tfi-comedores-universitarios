"""Cálculo de los totales de una caja a partir de sus comprobantes de venta."""
from decimal import Decimal

from django.db.models import Count, Sum

CENTAVOS = Decimal("0.01")
MEDIOS_DE_PAGO = ("efectivo", "tarjeta", "transferencia", "qr")


def _dinero(valor):
    return (valor or Decimal("0")).quantize(CENTAVOS)


def calcular_totales(caja):
    """
    Devuelve el resumen de ventas de la caja:

    - cantidad y total de comprobantes, en general y por medio de pago;
    - efectivo esperado = monto de apertura + ventas cobradas en efectivo.
      Las ventas con tarjeta, transferencia o QR no pasan por la caja física.

    Los comprobantes los carga el módulo de ventas (Comprobante.caja con
    related_name="comprobantes"). Mientras ese módulo no exista, los totales son cero.
    """
    por_medio = {m: {"cantidad": 0, "total": Decimal("0")} for m in MEDIOS_DE_PAGO}

    comprobantes = getattr(caja, "comprobantes", None)
    if comprobantes is not None:
        filas = comprobantes.values("medio_pago").annotate(
            cantidad=Count("id"), total=Sum("monto_total")
        )
        for fila in filas:
            medio = por_medio.setdefault(
                fila["medio_pago"], {"cantidad": 0, "total": Decimal("0")}
            )
            medio["cantidad"] = fila["cantidad"]
            medio["total"] = fila["total"] or Decimal("0")

    total_ventas = sum((m["total"] for m in por_medio.values()), Decimal("0"))
    cantidad = sum(m["cantidad"] for m in por_medio.values())
    efectivo_esperado = caja.monto_apertura + por_medio["efectivo"]["total"]

    return {
        "cantidad_comprobantes": cantidad,
        "total_ventas": _dinero(total_ventas),
        "por_medio_pago": {
            medio: {"cantidad": datos["cantidad"], "total": _dinero(datos["total"])}
            for medio, datos in por_medio.items()
        },
        "monto_apertura": _dinero(caja.monto_apertura),
        "efectivo_esperado": _dinero(efectivo_esperado),
    }


def _a_texto(valor):
    # Los importes viajan como texto ("1500.50"): un número decimal de JSON perdería precisión.
    if isinstance(valor, Decimal):
        return format(valor, "f")
    if isinstance(valor, dict):
        return {clave: _a_texto(item) for clave, item in valor.items()}
    return valor


def totales_para_api(caja):
    """Igual que calcular_totales, con los importes como texto para devolver en la API."""
    return _a_texto(calcular_totales(caja))
