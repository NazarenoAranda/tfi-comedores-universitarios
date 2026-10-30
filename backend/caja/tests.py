"""Pruebas automáticas de caja: apertura, cierre, totales y reglas de acceso por sede."""
from decimal import Decimal

from django.db import IntegrityError, transaction

from caja.models import Caja
from config.pruebas import PW, BaseApi, cliente
from usuarios.models import Usuario
from ventas.models import Comprobante


class CajaTests(BaseApi):
    def test_permisos(self):
        self.assertEqual(cliente().get("/api/cajas/").status_code, 401)
        co = self.login("compras@t.com")
        self.assertEqual(co.get("/api/cajas/").status_code, 403)
        self.assertEqual(co.post("/api/cajas/", {}, format="json").status_code, 403)

    def test_apertura_cajero(self):
        c = self.login("cajaA@t.com")
        r = c.post("/api/cajas/", {}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        d = r.json()
        self.assertEqual((d["sede"], d["usuario"], d["estado"]), (self.sedeA.pk, self.cajeroA.pk, "abierta"))
        self.assertEqual(d["monto_apertura"], "0.00"); self.assertIsNone(d["fecha_cierre"])
        self.assertEqual(d["totales"]["total_ventas"], "0.00"); self.assertEqual(d["totales"]["cantidad_comprobantes"], 0)
        # segunda apertura en la misma sede
        r = c.post("/api/cajas/", {"monto_apertura": 100}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("abierta", str(r.json()))

    def test_validaciones_apertura(self):
        c = self.login("cajaA@t.com"); a = self.login("admin@t.com")
        r = c.post("/api/cajas/", {"sede": self.sedeB.pk}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("sede", r.json())          # cajero en otra sede
        self.assertEqual(c.post("/api/cajas/", {"monto_apertura": -5}, format="json").status_code, 400)
        self.assertEqual(c.post("/api/cajas/", {"monto_apertura": "5000.505"}, format="json").status_code, 400)
        self.assertEqual(c.post("/api/cajas/", {"monto_apertura": "abc"}, format="json").status_code, 400)
        r = a.post("/api/cajas/", {}, format="json"); self.assertEqual(r.status_code, 400); self.assertIn("sede", r.json())
        r = a.post("/api/cajas/", {"sede": self.sedeC.pk}, format="json"); self.assertEqual(r.status_code, 400)
        r = a.post("/api/cajas/", {"sede": 9999}, format="json"); self.assertEqual(r.status_code, 400)
        r = a.post("/api/cajas/", {"sede": self.sedeB.pk, "monto_apertura": "1000.50"}, format="json")
        self.assertEqual(r.status_code, 201, r.content); self.assertEqual(r.json()["monto_apertura"], "1000.50")
        self.assertEqual(r.json()["usuario"], self.admin.pk)
        self.assertEqual(Caja.objects.count(), 1)

    def test_cajero_sin_sede(self):
        u = Usuario.objects.create_user("sinsede@t.com", PW, nombre="SS", rol="cajero")   # saltea la validación del serializer
        c = self.login("sinsede@t.com")
        self.assertEqual(c.get("/api/cajas/").json()["count"], 0)
        self.assertEqual(c.post("/api/cajas/", {}, format="json").status_code, 400)

    def test_aislamiento_por_sede(self):
        ca, cb, a = self.login("cajaA@t.com"), self.login("cajaB@t.com"), self.login("admin@t.com")
        idA = ca.post("/api/cajas/", {}, format="json").json()["id"]
        idB = cb.post("/api/cajas/", {}, format="json").json()["id"]
        self.assertEqual(ca.get("/api/cajas/").json()["count"], 1)
        self.assertEqual(ca.get(f"/api/cajas/{idB}/").status_code, 404)
        self.assertEqual(ca.get(f"/api/cajas/{idB}/totales/").status_code, 404)
        self.assertEqual(ca.post(f"/api/cajas/{idB}/cerrar/").status_code, 404)
        self.assertEqual(a.get("/api/cajas/").json()["count"], 2)
        self.assertEqual(a.get(f"/api/cajas/?sede={self.sedeB.pk}").json()["count"], 1)
        self.assertEqual(a.get("/api/cajas/?estado=abierta").json()["count"], 2)
        self.assertEqual(a.get("/api/cajas/?estado=cerrada").json()["count"], 0)
        self.assertEqual(a.get(f"/api/cajas/?usuario={self.cajeroA.pk}").json()["count"], 1)
        # actual
        self.assertEqual(ca.get("/api/cajas/actual/").json()["id"], idA)
        self.assertEqual(a.get("/api/cajas/actual/").status_code, 400)
        self.assertEqual(a.get(f"/api/cajas/actual/?sede={self.sedeB.pk}").json()["id"], idB)
        # no se modifica ni se borra por la API
        self.assertEqual(ca.delete(f"/api/cajas/{idA}/").status_code, 405)
        self.assertEqual(ca.patch(f"/api/cajas/{idA}/", {"estado": "cerrada"}, format="json").status_code, 405)

    def test_totales_y_cierre(self):
        c = self.login("cajaA@t.com")
        d = c.post("/api/cajas/", {"monto_apertura": "5000.50"}, format="json").json()
        caja = Caja.objects.get(pk=d["id"])
        for medio, monto in (("efectivo", "1000.50"), ("efectivo", "1000.00"), ("tarjeta", "3000.01"),
                             ("tarjeta", "0.10"), ("transferencia", "999.99"), ("qr", "450.25"), ("tarjeta", "0.20")):
            Comprobante.objects.create(caja=caja, sede=caja.sede, usuario=self.cajeroA, medio_pago=medio, monto_total=Decimal(monto))
        t = c.get(f"/api/cajas/{caja.pk}/totales/").json()
        self.assertEqual(t["cantidad_comprobantes"], 7)
        self.assertEqual(t["por_medio_pago"]["efectivo"], {"cantidad": 2, "total": "2000.50"})
        self.assertEqual(t["por_medio_pago"]["tarjeta"], {"cantidad": 3, "total": "3000.31"})
        self.assertEqual(t["total_ventas"], "6451.05")
        self.assertEqual(t["monto_apertura"], "5000.50"); self.assertEqual(t["efectivo_esperado"], "7001.00")
        self.assertEqual(c.get(f"/api/cajas/{caja.pk}/").json()["totales"]["total_ventas"], "6451.05")
        # cierre
        r = c.post(f"/api/cajas/{caja.pk}/cerrar/")
        self.assertEqual(r.status_code, 200, r.content)
        j = r.json()
        self.assertEqual((j["estado"], j["monto_cierre_calculado"]), ("cerrada", "7001.00"))
        self.assertIsNotNone(j["fecha_cierre"]); self.assertEqual(j["totales"]["efectivo_esperado"], "7001.00")
        r = c.post(f"/api/cajas/{caja.pk}/cerrar/"); self.assertEqual(r.status_code, 400); self.assertIn("cerrada", str(r.json()))
        self.assertEqual(c.get("/api/cajas/actual/").status_code, 404)
        # se puede abrir otra caja en la sede una vez cerrada la anterior
        self.assertEqual(c.post("/api/cajas/", {}, format="json").status_code, 201)
        self.assertEqual(Caja.objects.filter(sede=self.sedeA).count(), 2)

    def test_admin_cierra_cualquier_sede(self):
        cb = self.login("cajaB@t.com"); a = self.login("admin@t.com")
        idB = cb.post("/api/cajas/", {"monto_apertura": 10}, format="json").json()["id"]
        r = a.post(f"/api/cajas/{idB}/cerrar/")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["monto_cierre_calculado"], "10.00")

    def test_filtros_fecha(self):
        a = self.login("admin@t.com")
        a.post("/api/cajas/", {"sede": self.sedeA.pk}, format="json")
        self.assertEqual(a.get("/api/cajas/?desde=2000-01-01").json()["count"], 1)
        self.assertEqual(a.get("/api/cajas/?desde=2999-01-01").json()["count"], 0)
        self.assertEqual(a.get("/api/cajas/?hasta=2000-01-01").json()["count"], 0)
        self.assertEqual(a.get("/api/cajas/?hasta=2999-01-01").json()["count"], 1)
        self.assertEqual(a.get("/api/cajas/?desde=ayer").status_code, 400)

    def test_restricciones_de_base_de_datos(self):
        Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA)             # 2 abiertas en la misma sede
        with self.assertRaises(IntegrityError), transaction.atomic():
            Caja.objects.create(sede=self.sedeB, usuario=self.cajeroA, estado="rara")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Caja.objects.create(sede=self.sedeB, usuario=self.cajeroA, monto_apertura=Decimal("-1"))
        Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA, estado="cerrada")  # cerradas sí pueden ser varias
        Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA, estado="cerrada")

    def test_modelo_usuario_valida_cajero_sin_sede(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Usuario(nombre="x", email="x@t.com", rol="cajero").full_clean(exclude=["password"])
