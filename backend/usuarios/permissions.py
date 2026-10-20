"""
Permisos por rol. Se usan en las vistas de la API con `permission_classes`.

Roles: admin (administración), cajero y compras (encargado de compras).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _rol(request):
    usuario = request.user
    if usuario and usuario.is_authenticated:
        return usuario.rol
    return None


class EsAdmin(BasePermission):
    """Solo la administración."""

    message = "Solo la administración puede realizar esta acción."

    def has_permission(self, request, view):
        return _rol(request) == "admin"


class EsAdminOSoloLectura(BasePermission):
    """Cualquier usuario autenticado puede consultar; solo la administración modifica."""

    message = "Solo la administración puede modificar estos datos."

    def has_permission(self, request, view):
        rol = _rol(request)
        if rol is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return rol == "admin"


class EsAdminOCompras(BasePermission):
    """Administración y encargado de compras (consultan y modifican). El cajero no accede."""

    message = "Solo la administración y el encargado de compras pueden acceder a estos datos."

    def has_permission(self, request, view):
        return _rol(request) in ("admin", "compras")
