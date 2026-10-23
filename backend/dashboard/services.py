"""Cálculo de los totales de ventas y pedidos, por sede y consolidados."""
from decimal import Decimal

from django.db.models import Count, Sum

from config.utilidades import filtrar_por_fechas, texto_dinero
from pedidos.models import Pedido
from sedes.models import Sede
from ventas.models import Comprobante

MEDIOS_DE_PAGO = ("efectivo", "tarjeta", "transferencia", "qr")
ESTADOS = ("pendiente", "recibido", "cancelado")
CERO = Decimal("0")


def _ventas_vacias():
    return {m: {"cantidad": 0, "total": CERO} for m in MEDIOS_DE_PAGO}


def _pedidos_vacios():
    return {e: {"cantidad": 0, "total": CERO} for e in ESTADOS}


def _formatear_ventas(por_medio):
    return {
        "cantidad": sum(d["cantidad"] for d in por_medio.values()),
        "total": texto_dinero(sum((d["total"] for d in por_medio.values()), CERO)),
        "por_medio_pago": {
            m: {"cantidad": d["cantidad"], "total": texto_dinero(d["total"])} for m, d in por_medio.items()
        },
    }


def _formatear_pedidos(por_estado):
    # El total de pedidos no cuenta los cancelados: es lo que se compró o se va a pagar.
    vigentes = [d for estado, d in por_estado.items() if estado != "cancelado"]
    return {
        "cantidad": sum(d["cantidad"] for d in vigentes),
        "total": texto_dinero(sum((d["total"] for d in vigentes), CERO)),
        "por_estado": {
            e: {"cantidad": d["cantidad"], "total": texto_dinero(d["total"])} for e, d in por_estado.items()
        },
    }


def calcular_resumen(params, sede_id=None):
    """
    Devuelve ventas y pedidos agrupados por sede y consolidados.
    `params` son los parámetros de la URL (?desde=, ?hasta=); `sede_id` limita a una sede.
    Las ventas se filtran por la fecha del comprobante y los pedidos por la fecha del pedido.
    """
    comprobantes = Comprobante.objects.all()
    pedidos = Pedido.objects.all()
    if sede_id:
        comprobantes = comprobantes.filter(sede_id=sede_id)
        pedidos = pedidos.filter(sede_id=sede_id)
    comprobantes = filtrar_por_fechas(comprobantes, params, "fecha")
    pedidos = filtrar_por_fechas(pedidos, params, "fecha_pedido")

    ventas = {}   # sede_id -> medio -> datos
    for fila in comprobantes.order_by().values("sede_id", "medio_pago").annotate(
        cantidad=Count("id"), total=Sum("monto_total")
    ):
        medios = ventas.setdefault(fila["sede_id"], _ventas_vacias())
        medios[fila["medio_pago"]] = {"cantidad": fila["cantidad"], "total": fila["total"] or CERO}

    pedidos_por_sede = {}   # sede_id -> estado -> datos
    for fila in pedidos.order_by().values("sede_id", "estado").annotate(
        cantidad=Count("id"), total=Sum("monto_total")
    ):
        estados = pedidos_por_sede.setdefault(fila["sede_id"], _pedidos_vacios())
        estados[fila["estado"]] = {"cantidad": fila["cantidad"], "total": fila["total"] or CERO}

    # Se muestran las sedes activas (aunque no tengan movimientos) y las dadas de baja que
    # tengan movimientos en el período.
    sedes = Sede.objects.all()
    if sede_id:
        sedes = sedes.filter(pk=sede_id)
    con_movimientos = set(ventas) | set(pedidos_por_sede)
    sedes = [s for s in sedes.order_by("nombre", "id") if s.activa or s.pk in con_movimientos]

    por_sede = []
    total_ventas = _ventas_vacias()
    total_pedidos = _pedidos_vacios()
    for sede in sedes:
        v = ventas.get(sede.pk, _ventas_vacias())
        p = pedidos_por_sede.get(sede.pk, _pedidos_vacios())
        for m, d in v.items():
            total_ventas[m]["cantidad"] += d["cantidad"]
            total_ventas[m]["total"] += d["total"]
        for e, d in p.items():
            total_pedidos[e]["cantidad"] += d["cantidad"]
            total_pedidos[e]["total"] += d["total"]
        vf, pf = _formatear_ventas(v), _formatear_pedidos(p)
        por_sede.append(
            {
                "sede": sede.pk,
                "sede_nombre": sede.nombre,
                "ventas": vf,
                "pedidos": pf,
                "resultado": texto_dinero(
                    sum((d["total"] for d in v.values()), CERO)
                    - sum((d["total"] for e, d in p.items() if e != "cancelado"), CERO)
                ),
            }
        )

    consolidado = {
        "ventas": _formatear_ventas(total_ventas),
        "pedidos": _formatear_pedidos(total_pedidos),
        "resultado": texto_dinero(
            sum((d["total"] for d in total_ventas.values()), CERO)
            - sum((d["total"] for e, d in total_pedidos.items() if e != "cancelado"), CERO)
        ),
    }
    return consolidado, por_sede
