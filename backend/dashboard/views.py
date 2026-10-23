from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from config.utilidades import rango_de_fechas
from sedes.models import Sede
from usuarios.permissions import EsAdmin

from .services import calcular_resumen


class ResumenView(APIView):
    """
    Panel consolidado (solo administración).

    GET /api/dashboard/resumen/   totales de ventas y pedidos, por sede y consolidados.
                                  Filtros: ?sede=<id>, ?desde=AAAA-MM-DD, ?hasta=AAAA-MM-DD
                                  (ventas por fecha del comprobante, pedidos por fecha del pedido).
    """

    permission_classes = [EsAdmin]

    def get(self, request):
        params = request.query_params
        desde, hasta = rango_de_fechas(params)  # valida las fechas antes de calcular
        sede_id = params.get("sede")
        if sede_id:
            if not sede_id.isdigit() or not Sede.objects.filter(pk=sede_id).exists():
                raise ValidationError({"sede": "La sede no existe."})
        consolidado, por_sede = calcular_resumen(params, sede_id)
        return Response(
            {
                "desde": desde.isoformat() if desde else None,
                "hasta": hasta.isoformat() if hasta else None,
                "consolidado": consolidado,
                "por_sede": por_sede,
            }
        )
