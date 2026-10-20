from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from usuarios.permissions import EsAdminOCajero

from .models import Caja
from .serializers import CajaDetalleSerializer, CajaSerializer
from .services import calcular_totales, totales_para_api


class CajaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Apertura y cierre de caja. Lo usan los cajeros (solo ven las cajas de su sede) y la
    administración (ve todas). Las cajas no se modifican ni se borran por la API.

    - GET  /api/cajas/                 listado (filtros: ?sede=, ?estado=, ?usuario=, ?desde=AAAA-MM-DD, ?hasta=AAAA-MM-DD)
    - POST /api/cajas/                 apertura: {"monto_apertura": 5000, "sede": <id, solo admin>}
    - GET  /api/cajas/<id>/            detalle, con el resumen de ventas
    - GET  /api/cajas/actual/          caja abierta de la sede (admin: ?sede=<id>)
    - GET  /api/cajas/<id>/totales/    resumen de ventas de la caja
    - POST /api/cajas/<id>/cerrar/     cierre: calcula los totales y deja la caja cerrada
    """

    permission_classes = [EsAdminOCajero]

    def get_serializer_class(self):
        if self.action == "list":
            return CajaSerializer
        if self.action == "create":
            return CajaSerializer
        return CajaDetalleSerializer

    def get_queryset(self):
        queryset = Caja.objects.select_related("sede", "usuario")
        usuario = self.request.user
        if usuario.rol == "cajero":
            # Un cajero solo ve las cajas de su sede.
            queryset = queryset.filter(sede_id=usuario.sede_id) if usuario.sede_id else queryset.none()

        params = self.request.query_params
        if params.get("sede"):
            queryset = queryset.filter(sede_id=params["sede"])
        if params.get("estado"):
            queryset = queryset.filter(estado=params["estado"])
        if params.get("usuario"):
            queryset = queryset.filter(usuario_id=params["usuario"])
        for parametro, filtro in (("desde", "fecha_apertura__date__gte"), ("hasta", "fecha_apertura__date__lte")):
            valor = params.get(parametro)
            if valor:
                fecha = parse_date(valor)
                if fecha is None:
                    raise ValidationError({parametro: "Formato de fecha inválido. Usar AAAA-MM-DD."})
                queryset = queryset.filter(**{filtro: fecha})
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(usuario=self.request.user)
        except IntegrityError:
            # Dos aperturas simultáneas en la misma sede: la base de datos rechaza la segunda.
            raise ValidationError("Ya hay una caja abierta en esta sede.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        caja = Caja.objects.select_related("sede", "usuario").get(pk=serializer.instance.pk)
        return Response(CajaDetalleSerializer(caja, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def actual(self, request):
        queryset = self.get_queryset().filter(estado=Caja.Estado.ABIERTA)
        if request.user.rol != "cajero" and not request.query_params.get("sede"):
            raise ValidationError({"sede": "Indicá la sede con ?sede=<id>."})
        caja = queryset.first()
        if caja is None:
            return Response({"detail": "No hay una caja abierta."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(caja).data)

    @action(detail=True, methods=["get"])
    def totales(self, request, pk=None):
        return Response(totales_para_api(self.get_object()))

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        caja = self.get_object()  # ya aplica el filtro por sede del cajero
        with transaction.atomic():
            # Se bloquea la fila para que dos cierres simultáneos no se pisen.
            caja = Caja.objects.select_for_update().get(pk=caja.pk)
            if caja.estado != Caja.Estado.ABIERTA:
                raise ValidationError("La caja ya está cerrada.")
            totales = calcular_totales(caja)
            caja.monto_cierre_calculado = totales["efectivo_esperado"]
            caja.fecha_cierre = timezone.now()
            caja.estado = Caja.Estado.CERRADA
            caja.save(update_fields=["monto_cierre_calculado", "fecha_cierre", "estado"])
        caja = Caja.objects.select_related("sede", "usuario").get(pk=caja.pk)
        return Response(self.get_serializer(caja).data)
