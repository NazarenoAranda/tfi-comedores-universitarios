"""Pruebas automáticas de pedidos a proveedores: alta con ítems, estados (pendiente, recibido, cancelado), permisos y filtros."""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from pedidos.models import Pedido
from proveedores.models import Proveedor
from sedes.models import Sede
from usuarios.models import Usuario

PW = "Clave-segura-123"
HASH_RAPIDO = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # solo en pruebas: las acelera


def cliente(token=None):
    c = APIClient()
    if token:
        c.credentials(HTTP_AUTHORIZATION="Token " + token)
    return c


ITEMS = [{"descripcion": "Harina 25kg", "cantidad": 4, "precio_unitario": "12000.50"},
         {"descripcion": "Aceite", "cantidad": 2, "precio_unitario": "3500"}]


@override_settings(PASSWORD_HASHERS=HASH_RAPIDO)
class PedidosTests(APITestCase):
    def setUp(self):
        self.sede = Sede.objects.create(nombre="Central")
        self.sede2 = Sede.objects.create(nombre="Norte")
        self.baja = Sede.objects.create(nombre="Vieja", activa=False)
        self.prov = Proveedor.objects.create(nombre="Molinos")
        self.prov2 = Proveedor.objects.create(nombre="Lácteos")
        self.provbaja = Proveedor.objects.create(nombre="Cerrado", activo=False)
        self.admin = Usuario.objects.create_superuser("admin@t.com", PW, nombre="Admin")
        self.compras = Usuario.objects.create_user("c@t.com", PW, nombre="Compras", rol="compras")
        self.cajero = Usuario.objects.create_user("a@t.com", PW, nombre="Caja", rol="cajero", sede=self.sede)

    def login(self, email):
        r = APIClient().post("/api/auth/login/", {"email": email, "password": PW}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return cliente(r.json()["token"])

    def alta(self, c=None, **extra):
        c = c or self.login("c@t.com")
        body = {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": ITEMS}
        body.update(extra)
        return c.post("/api/pedidos/", body, format="json")

    def test_alta_calcula_total_y_estado(self):
        r = self.alta()
        self.assertEqual(r.status_code, 201, r.content)
        d = r.json()
        self.assertEqual(d["estado"], "pendiente")
        self.assertEqual(d["monto_total"], "55002.00")
        self.assertIsNone(d["fecha_recibido"])
        self.assertEqual(d["usuario"], self.compras.pk)
        self.assertEqual(d["proveedor_nombre"], "Molinos")
        self.assertEqual(len(d["items"]), 2)
        self.assertEqual(d["items"][0]["subtotal"], "48002.00")

    def test_admin_tambien_crea(self):
        self.assertEqual(self.alta(self.login("admin@t.com")).status_code, 201)

    def test_campos_solo_lectura_ignorados(self):
        r = self.alta(estado="recibido", monto_total="1", usuario=self.admin.pk, fecha_recibido="2020-01-01T00:00:00Z")
        d = r.json()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(d["estado"], "pendiente")
        self.assertEqual(d["monto_total"], "55002.00")
        self.assertEqual(d["usuario"], self.compras.pk)
        self.assertIsNone(d["fecha_recibido"])

    def test_validaciones(self):
        c = self.login("c@t.com")
        malos = [
            {"proveedor": self.prov.pk, "sede": self.sede.pk},
            {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": []},
            {"proveedor": self.provbaja.pk, "sede": self.sede.pk, "items": ITEMS},
            {"proveedor": self.prov.pk, "sede": self.baja.pk, "items": ITEMS},
            {"proveedor": 9999, "sede": self.sede.pk, "items": ITEMS},
            {"sede": self.sede.pk, "items": ITEMS},
            {"proveedor": self.prov.pk, "items": ITEMS},
            {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": [{"descripcion": "x", "cantidad": 0, "precio_unitario": "1"}]},
            {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "-1"}]},
            {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "0"}]},
            {"proveedor": self.prov.pk, "sede": self.sede.pk, "items": [{"descripcion": "", "cantidad": 1, "precio_unitario": "5"}]},
        ]
        for b in malos:
            self.assertEqual(c.post("/api/pedidos/", b, format="json").status_code, 400, b)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_permisos(self):
        self.assertEqual(cliente().get("/api/pedidos/").status_code, 401)
        a = self.login("a@t.com")
        self.assertEqual(a.get("/api/pedidos/").status_code, 403)
        self.assertEqual(self.alta(a).status_code, 403)
        pk = self.alta().json()["id"]
        self.assertEqual(a.post(f"/api/pedidos/{pk}/recibir/").status_code, 403)
        self.assertEqual(a.get(f"/api/pedidos/{pk}/").status_code, 403)

    def test_recibir(self):
        c = self.login("c@t.com")
        pk = self.alta(c).json()["id"]
        r = c.post(f"/api/pedidos/{pk}/recibir/")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["estado"], "recibido")
        self.assertIsNotNone(r.json()["fecha_recibido"])
        for accion in ("recibir", "cancelar"):
            self.assertEqual(c.post(f"/api/pedidos/{pk}/{accion}/").status_code, 400)
        self.assertEqual(Pedido.objects.get(pk=pk).estado, "recibido")

    def test_cancelar(self):
        c = self.login("c@t.com")
        pk = self.alta(c).json()["id"]
        r = c.post(f"/api/pedidos/{pk}/cancelar/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["estado"], "cancelado")
        self.assertIsNone(r.json()["fecha_recibido"])
        self.assertEqual(c.post(f"/api/pedidos/{pk}/recibir/").status_code, 400)
        self.assertEqual(c.post("/api/pedidos/99999/recibir/").status_code, 404)

    def test_sin_modificar_ni_borrar(self):
        c = self.login("admin@t.com")
        pk = self.alta(c).json()["id"]
        self.assertEqual(c.put(f"/api/pedidos/{pk}/", {}, format="json").status_code, 405)
        self.assertEqual(c.patch(f"/api/pedidos/{pk}/", {}, format="json").status_code, 405)
        self.assertEqual(c.delete(f"/api/pedidos/{pk}/").status_code, 405)

    def test_filtros(self):
        c = self.login("c@t.com")
        a = self.alta(c).json()["id"]
        b = self.alta(c, proveedor=self.prov2.pk, sede=self.sede2.pk).json()["id"]
        Pedido.objects.filter(pk=b).update(fecha_pedido=timezone.now() - timedelta(days=10))
        c.post(f"/api/pedidos/{b}/cancelar/")
        q = lambda s: c.get("/api/pedidos/?" + s).json()["count"]
        self.assertEqual(q(""), 2)
        self.assertEqual(q(f"sede={self.sede.pk}"), 1)
        self.assertEqual(q(f"proveedor={self.prov2.pk}"), 1)
        self.assertEqual(q("estado=cancelado"), 1)
        self.assertEqual(q("estado=pendiente"), 1)
        h = timezone.localtime(timezone.now()).date()
        d5 = (h - timedelta(days=5)).isoformat()
        self.assertEqual(q(f"desde={d5}"), 1)
        self.assertEqual(q(f"hasta={d5}"), 1)
        self.assertEqual(q(f"desde={d5}&estado=pendiente"), 1)
        self.assertEqual(c.get("/api/pedidos/?desde=x").status_code, 400)
        self.assertEqual(c.get("/api/pedidos/?desde=2026-05-02&hasta=2026-05-01").status_code, 400)
        res = c.get("/api/pedidos/").json()["results"]
        self.assertEqual([x["id"] for x in res], [a, b])  # más nuevo primero

    def test_restricciones_y_proteccion(self):
        p = Pedido.objects.create(proveedor=self.prov, sede=self.sede, usuario=self.compras)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Pedido.objects.filter(pk=p.pk).update(estado="otro")
        with self.assertRaises(ProtectedError):
            self.prov.delete()
        with self.assertRaises(ProtectedError):
            self.sede.delete()
