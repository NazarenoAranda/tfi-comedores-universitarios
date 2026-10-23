"""Funciones de uso común en las vistas de la API: fechas de los filtros e importes."""
from decimal import Decimal

from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

CENTAVOS = Decimal("0.01")


def texto_dinero(valor):
    """Importe como texto con dos decimales ("1500.50"). En JSON un número perdería precisión."""
    return format((valor or Decimal("0")).quantize(CENTAVOS), "f")


def fecha_de_parametro(params, nombre):
    """Lee una fecha AAAA-MM-DD de los parámetros de la URL. Devuelve None si no viene."""
    valor = params.get(nombre)
    if not valor:
        return None
    try:
        fecha = parse_date(valor)
    except ValueError:  # formato correcto pero fecha inexistente, por ejemplo 2026-02-31
        fecha = None
    if fecha is None:
        raise ValidationError({nombre: "Fecha inválida. Usar el formato AAAA-MM-DD."})
    return fecha


def rango_de_fechas(params):
    """Devuelve (desde, hasta) de los parámetros ?desde= y ?hasta=, validando que estén en orden."""
    desde = fecha_de_parametro(params, "desde")
    hasta = fecha_de_parametro(params, "hasta")
    if desde and hasta and desde > hasta:
        raise ValidationError({"desde": "No puede ser posterior a la fecha 'hasta'."})
    return desde, hasta


def filtrar_por_fechas(queryset, params, campo):
    """Filtra el queryset por ?desde= y ?hasta= (ambos inclusivos) según el día del campo de fecha."""
    desde, hasta = rango_de_fechas(params)
    if desde:
        queryset = queryset.filter(**{f"{campo}__date__gte": desde})
    if hasta:
        queryset = queryset.filter(**{f"{campo}__date__lte": hasta})
    return queryset
