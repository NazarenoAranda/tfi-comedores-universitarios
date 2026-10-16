from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    """Chequeo de estado: público, sirve para verificar que la API y la base responden."""
    try:
        connection.ensure_connection()
        base_de_datos = "ok"
    except Exception:
        base_de_datos = "error"
    estado = "ok" if base_de_datos == "ok" else "error"
    return Response(
        {"status": estado, "database": base_de_datos},
        status=200 if estado == "ok" else 503,
    )
