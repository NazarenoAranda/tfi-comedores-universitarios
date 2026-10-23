from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from config.utilidades import filtrar_por_fechas
from usuarios.permissions import EsAdminOCajero

from .models import Comprobante
from .serializers import ComprobanteSerializer


class ComprobanteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Comprobantes de venta. Los cargan los cajeros (en la caja abierta de su sede, y solo ven
    los de su sede) y la administración (indicando la caja; ve todos). Los comprobantes no se
    modifican ni se borran por la API: son el respaldo del cierre de caja.

    - GET  /api/comprobantes/        listado, del más nuevo al más viejo
                                     (filtros: ?sede=, ?caja=, ?medio_pago=, ?usuario=,
                                      ?desde=AAAA-MM-DD, ?hasta=AAAA-MM-DD)
    - POST /api/comprobantes/        alta: {"medio_pago": "efectivo", "items": [...]} o
                                     {"medio_pago": "qr", "monto_total": 1500}
                                     (la administración agrega "caja": <id>)
    - GET  /api/comprobantes/<id>/   detalle
    """

    serializer_class = ComprobanteSerializer
    permission_classes = [EsAdminOCajero]

    def get_queryset(self):
        queryset = Comprobante.objects.select_related("sede", "usuario", "caja").prefetch_related("items")
        usuario = self.request.user
        if usuario.rol == "cajero":
            # Un cajero solo ve los comprobantes de su sede.
            queryset = queryset.filter(sede_id=usuario.sede_id) if usuario.sede_id else queryset.none()

        params = self.request.query_params
        for parametro, campo in (
            ("sede", "sede_id"),
            ("caja", "caja_id"),
            ("usuario", "usuario_id"),
            ("medio_pago", "medio_pago"),
        ):
            valor = params.get(parametro)
            if valor:
                queryset = queryset.filter(**{campo: valor})
        return filtrar_por_fechas(queryset, params, "fecha")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comprobante = serializer.save()
        # Se vuelve a leer con sus relaciones para devolver el comprobante completo.
        comprobante = self.get_queryset().get(pk=comprobante.pk)
        return Response(self.get_serializer(comprobante).data, status=status.HTTP_201_CREATED)
