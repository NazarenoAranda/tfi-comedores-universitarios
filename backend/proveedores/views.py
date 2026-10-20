from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from usuarios.permissions import EsAdminOCompras

from .models import Proveedor
from .serializers import ProveedorSerializer


class ProveedorViewSet(viewsets.ModelViewSet):
    """
    ABM de proveedores. Lo usan la administración y el encargado de compras.

    - GET    /api/proveedores/          listado (filtros: ?activo=true|false, ?search=texto)
    - POST   /api/proveedores/          alta
    - GET    /api/proveedores/<id>/     detalle
    - PUT/PATCH /api/proveedores/<id>/  modificación
    - DELETE /api/proveedores/<id>/     baja lógica (el proveedor queda inactivo, no se borra)
    """

    serializer_class = ProveedorSerializer
    permission_classes = [EsAdminOCompras]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "contacto", "email", "telefono"]

    def get_queryset(self):
        queryset = Proveedor.objects.all()
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.strip().lower() in ("1", "true", "yes", "si"))
        return queryset

    def destroy(self, request, *args, **kwargs):
        proveedor = self.get_object()
        proveedor.activo = False
        proveedor.save(update_fields=["activo"])
        return Response(status=status.HTTP_204_NO_CONTENT)
