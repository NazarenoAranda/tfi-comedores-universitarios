"""Pruebas automáticas del panel consolidado: totales por sede y consolidados, filtros y permisos."""
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from caja.models import Caja
from pedidos.models import Pedido
from proveedores.models import Proveedor
from sedes.models import Sede
from usuarios.models import Usuario
from ventas.models import Comprobante

PW = "Clave-segura-123"
HASH_RAPIDO = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # solo en pruebas: las acelera


@override_settings(PASSWORD_HASHERS=HASH_RAPIDO)
class DashboardTests(APITestCase):
    def setUp(self):
        self.s1 = Sede.objects.create(nombre="Central")
        self.s2 = Sede.objects.create(nombre="Norte")
        self.s3 = Sede.objects.create(nombre="Sin movimientos")
        self.s4 = Sede.objects.create(nombre="Baja con datos", activa=False)
        self.s5 = Sede.objects.create(nombre="Baja sin datos", activa=False)
        self.admin = Usuario.objects.create_superuser("admin@t.com", PW, nombre="Admin")
        self.cajero = Usuario.objects.create_user("a@t.com", PW, nombre="C", rol="cajero", sede=self.s1)
        self.compras = Usuario.objects.create_user("c@t.com", PW, nombre="P", rol="compras")
        self.prov = Proveedor.objects.create(nombre="Prov")
        ahora = timezone.now()
        cajas = {s: Caja.objects.create(sede=s, usuario=self.admin) for s in (self.s1, self.s2, self.s4)}
        for sede, medio, monto, dias in [
            (self.s1, "efectivo", "100.10", 0), (self.s1, "efectivo", "200", 0), (self.s1, "qr", "50.05", 0),
            (self.s1, "tarjeta", "1000", 20), (self.s2, "transferencia", "300", 0), (self.s4, "efectivo", "10", 0)]:
            Comprobante.objects.create(caja=cajas[sede], sede=sede, usuario=self.admin, medio_pago=medio,
                                       monto_total=Decimal(monto), fecha=ahora - timedelta(days=dias))
        for sede, estado, monto, dias in [
            (self.s1, "pendiente", "70", 0), (self.s1, "recibido", "30", 0), (self.s1, "cancelado", "999", 0),
            (self.s2, "recibido", "500", 20)]:
            Pedido.objects.create(proveedor=self.prov, sede=sede, usuario=self.admin, estado=estado,
                                  monto_total=Decimal(monto), fecha_pedido=ahora - timedelta(days=dias))

    def login(self, email):
        r = APIClient().post("/api/auth/login/", {"email": email, "password": PW}, format="json")
        c = APIClient(); c.credentials(HTTP_AUTHORIZATION="Token " + r.json()["token"]); return c

    def get(self, q=""):
        r = self.login("admin@t.com").get("/api/dashboard/resumen/" + q)
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_permisos(self):
        self.assertEqual(APIClient().get("/api/dashboard/resumen/").status_code, 401)
        for e in ("a@t.com", "c@t.com"):
            self.assertEqual(self.login(e).get("/api/dashboard/resumen/").status_code, 403)

    def test_consolidado_y_por_sede(self):
        d = self.get()
        c = d["consolidado"]
        self.assertEqual(c["ventas"]["cantidad"], 6)
        self.assertEqual(c["ventas"]["total"], "1660.15")
        self.assertEqual(c["ventas"]["por_medio_pago"]["efectivo"], {"cantidad": 3, "total": "310.10"})
        self.assertEqual(c["ventas"]["por_medio_pago"]["transferencia"]["total"], "300.00")
        self.assertEqual(c["pedidos"]["cantidad"], 3)            # sin cancelados
        self.assertEqual(c["pedidos"]["total"], "600.00")        # 70 + 30 + 500
        self.assertEqual(c["pedidos"]["por_estado"]["cancelado"], {"cantidad": 1, "total": "999.00"})
        self.assertEqual(c["resultado"], "1060.15")
        nombres = [s["sede_nombre"] for s in d["por_sede"]]
        self.assertEqual(nombres, ["Baja con datos", "Central", "Norte", "Sin movimientos"])  # sin la baja sin datos
        por = {s["sede_nombre"]: s for s in d["por_sede"]}
        c1 = por["Central"]
        self.assertEqual(c1["ventas"]["total"], "1350.15")
        self.assertEqual(c1["pedidos"]["total"], "100.00")
        self.assertEqual(c1["resultado"], "1250.15")
        self.assertEqual(por["Sin movimientos"]["ventas"]["total"], "0.00")
        self.assertEqual(por["Sin movimientos"]["pedidos"]["por_estado"]["pendiente"]["cantidad"], 0)
        # el consolidado es la suma de las sedes
        self.assertEqual(sum(Decimal(s["ventas"]["total"]) for s in d["por_sede"]), Decimal(c["ventas"]["total"]))
        self.assertEqual(sum(Decimal(s["pedidos"]["total"]) for s in d["por_sede"]), Decimal(c["pedidos"]["total"]))

    def test_filtros(self):
        h = timezone.localtime(timezone.now()).date()
        d10 = (h - timedelta(days=10)).isoformat()
        d = self.get(f"?desde={d10}")
        self.assertEqual(d["consolidado"]["ventas"]["total"], "660.15")      # sin la venta de hace 20 días
        self.assertEqual(d["consolidado"]["pedidos"]["total"], "100.00")
        self.assertEqual(d["desde"], d10); self.assertIsNone(d["hasta"])
        d = self.get(f"?hasta={d10}")
        self.assertEqual(d["consolidado"]["ventas"]["total"], "1000.00")
        self.assertEqual(d["consolidado"]["pedidos"]["total"], "500.00")
        d = self.get(f"?sede={self.s2.pk}")
        self.assertEqual([s["sede_nombre"] for s in d["por_sede"]], ["Norte"])
        self.assertEqual(d["consolidado"]["ventas"]["total"], "300.00")
        d = self.get(f"?sede={self.s3.pk}")
        self.assertEqual(d["consolidado"]["ventas"]["total"], "0.00")
        self.assertEqual(d["consolidado"]["resultado"], "0.00")

    def test_parametros_invalidos(self):
        c = self.login("admin@t.com")
        for q in ("desde=x", "hasta=2026-02-31", "desde=2026-05-02&hasta=2026-05-01", "sede=999", "sede=abc"):
            self.assertEqual(c.get("/api/dashboard/resumen/?" + q).status_code, 400, q)

    def test_sin_datos(self):
        Comprobante.objects.all().delete(); Pedido.objects.all().delete()
        d = self.get()
        self.assertEqual(d["consolidado"]["ventas"]["total"], "0.00")
        self.assertEqual(d["consolidado"]["pedidos"]["cantidad"], 0)
        self.assertEqual(len(d["por_sede"]), 3)

    def test_pocas_consultas(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        c = self.login("admin@t.com")
        with CaptureQueriesContext(connection) as q:
            c.get("/api/dashboard/resumen/")
        self.assertLessEqual(len(q), 8, [x["sql"][:60] for x in q])
