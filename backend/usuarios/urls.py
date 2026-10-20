from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import LoginView, LogoutView, MeView, UsuarioViewSet

router = SimpleRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    *router.urls,
]
