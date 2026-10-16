from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from .models import Sede
from .serializers import SedeSerializer


class SedeViewSet(viewsets.ModelViewSet):
    """
    ABM de sedes.

    - GET    /api/sedes/          listado (filtros: ?activa=true|false, ?search=texto)
    - POST   /api/sedes/          alta
    - GET    /api/sedes/<id>/     detalle
    - PUT/PATCH /api/sedes/<id>/  modificación
    - DELETE /api/sedes/<id>/     baja lógica (la sede queda inactiva, no se borra)
    """

    serializer_class = SedeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "universidad", "direccion"]

    def get_queryset(self):
        queryset = Sede.objects.all()
        activa = self.request.query_params.get("activa")
        if activa is not None:
            queryset = queryset.filter(activa=activa.strip().lower() in ("1", "true", "yes", "si"))
        return queryset

    def destroy(self, request, *args, **kwargs):
        sede = self.get_object()
        sede.activa = False
        sede.save(update_fields=["activa"])
        return Response(status=status.HTTP_204_NO_CONTENT)
