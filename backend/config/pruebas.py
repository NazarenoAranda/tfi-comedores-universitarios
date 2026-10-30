"""
Base común de las pruebas automáticas del backend.

Crea un escenario chico y siempre igual: 3 sedes (una dada de baja), un administrador,
un cajero por sede (A y B), un usuario de compras. Todos con la misma contraseña.

Las pruebas usan un cifrador de contraseñas rápido (solo durante las pruebas) para que
corran en segundos; en el sistema real Django usa su cifrador seguro por defecto.
"""
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from sedes.models import Sede
from usuarios.models import Usuario

PW = "Clave-segura-123"
HASH_RAPIDO = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def cliente(token=None):
    """Cliente de la API; con `token` envía el header Authorization de un usuario ya logueado."""
    c = APIClient()
    if token:
        c.credentials(HTTP_AUTHORIZATION="Token " + token)
    return c


@override_settings(PASSWORD_HASHERS=HASH_RAPIDO)
class BaseApi(APITestCase):
    def setUp(self):
        self.sedeA = Sede.objects.create(nombre="Central", universidad="UTN")
        self.sedeB = Sede.objects.create(nombre="Norte", universidad="UBA")
        self.sedeC = Sede.objects.create(nombre="Cerrada", activa=False)
        self.admin = Usuario.objects.create_superuser("admin@t.com", PW, nombre="Admin")
        self.cajeroA = Usuario.objects.create_user("cajaA@t.com", PW, nombre="CajaA", rol="cajero", sede=self.sedeA)
        self.cajeroB = Usuario.objects.create_user("cajaB@t.com", PW, nombre="CajaB", rol="cajero", sede=self.sedeB)
        self.compras = Usuario.objects.create_user("compras@t.com", PW, nombre="Compras", rol="compras")

    def login(self, email, pw=PW):
        """Inicia sesión por la API (como lo hace el frontend) y devuelve un cliente con el token."""
        r = APIClient().post("/api/auth/login/", {"email": email, "password": pw}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return cliente(r.json()["token"])
