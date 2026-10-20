from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Usuario
from .permissions import EsAdmin
from .serializers import LoginSerializer, UsuarioAdminSerializer, UsuarioSerializer


class LoginView(APIView):
    """POST /api/auth/login/ — recibe email y password y devuelve el token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["usuario"]
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response({"token": token.key, "usuario": UsuarioSerializer(usuario).data})


class LogoutView(APIView):
    """POST /api/auth/logout/ — invalida el token con el que se hizo el pedido."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.auth is not None:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ — datos del usuario que inició sesión."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    Gestión de usuarios (solo administración).

    - GET    /api/usuarios/          listado (filtros: ?rol=, ?sede=, ?activo=true|false, ?search=)
    - POST   /api/usuarios/          alta
    - GET    /api/usuarios/<id>/     detalle
    - PUT/PATCH /api/usuarios/<id>/  modificación (la contraseña es opcional)
    - DELETE /api/usuarios/<id>/     baja lógica: el usuario queda inactivo y no se borra
    """

    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "email"]

    def get_queryset(self):
        queryset = Usuario.objects.select_related("sede").order_by("nombre")
        params = self.request.query_params
        if params.get("rol"):
            queryset = queryset.filter(rol=params["rol"])
        if params.get("sede"):
            queryset = queryset.filter(sede_id=params["sede"])
        activo = params.get("activo")
        if activo is not None:
            queryset = queryset.filter(
                is_active=activo.strip().lower() in ("1", "true", "yes", "si")
            )
        return queryset

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            return Response(
                {"detail": "No podés dar de baja tu propio usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        Token.objects.filter(user=usuario).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
