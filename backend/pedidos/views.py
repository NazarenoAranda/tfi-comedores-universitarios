from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from config.utilidades import filtrar_por_fechas
from usuarios.permissions import EsAdminOCompras

from .models import Pedido
from .serializers import PedidoSerializer


class PedidoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Pedidos a proveedores. Los registran compras y la administración. Un pedido nace
    `pendiente` y pasa a `recibido` o `cancelado`; no se modifica ni se borra: para corregir
    un pedido pendiente se cancela y se carga uno nuevo.

    - GET  /api/pedidos/                 listado, del más nuevo al más viejo
                                         (filtros: ?sede=, ?proveedor=, ?estado=, ?usuario=,
                                          ?desde=AAAA-MM-DD, ?hasta=AAAA-MM-DD sobre la fecha del pedido)
    - POST /api/pedidos/                 alta: {"proveedor": 1, "sede": 1, "items": [...]}
    - GET  /api/pedidos/<id>/            detalle
    - POST /api/pedidos/<id>/recibir/    marca el pedido como recibido (guarda la fecha de recepción)
    - POST /api/pedidos/<id>/cancelar/   cancela un pedido pendiente
    """

    serializer_class = PedidoSerializer
    permission_classes = [EsAdminOCompras]

    def get_queryset(self):
        queryset = Pedido.objects.select_related("proveedor", "sede", "usuario").prefetch_related("items")
        params = self.request.query_params
        for parametro, campo in (
            ("sede", "sede_id"),
            ("proveedor", "proveedor_id"),
            ("usuario", "usuario_id"),
            ("estado", "estado"),
        ):
            valor = params.get(parametro)
            if valor:
                queryset = queryset.filter(**{campo: valor})
        return filtrar_por_fechas(queryset, params, "fecha_pedido")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        pedido = self.get_queryset().get(pk=pedido.pk)
        return Response(self.get_serializer(pedido).data, status=status.HTTP_201_CREATED)

    def _cambiar_estado(self, pedido_id, nuevo_estado):
        with transaction.atomic():
            # Se bloquea la fila para que dos cambios simultáneos no se pisen.
            pedido = Pedido.objects.select_for_update().get(pk=pedido_id)
            if pedido.estado != Pedido.Estado.PENDIENTE:
                raise ValidationError(
                    f"Solo se puede cambiar un pedido pendiente (este está {pedido.get_estado_display().lower()})."
                )
            pedido.estado = nuevo_estado
            campos = ["estado"]
            if nuevo_estado == Pedido.Estado.RECIBIDO:
                pedido.fecha_recibido = timezone.now()
                campos.append("fecha_recibido")
            pedido.save(update_fields=campos)
        return Response(self.get_serializer(self.get_queryset().get(pk=pedido_id)).data)

    @action(detail=True, methods=["post"])
    def recibir(self, request, pk=None):
        pedido = self.get_object()
        return self._cambiar_estado(pedido.pk, Pedido.Estado.RECIBIDO)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        pedido = self.get_object()
        return self._cambiar_estado(pedido.pk, Pedido.Estado.CANCELADO)
