"""Pruebas automáticas de ventas: alta de comprobantes (con y sin ítems), reglas de caja abierta,
permisos por rol, filtros y relación con el cierre de caja."""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from caja.models import Caja
from config.pruebas import PW, BaseApi, cliente
from usuarios.models import Usuario
from ventas.models import Comprobante


class VentasTests(BaseApi):
    def setUp(self):
        super().setUp()
        self.sinsede = Usuario.objects.create_user("sinsede@t.com", PW, nombre="Sin", rol="cajero")
        self.cajaA = Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA, monto_apertura=Decimal("1000"))
        self.cajaB = Caja.objects.create(sede=self.sedeB, usuario=self.cajeroB, monto_apertura=Decimal("0"))

    def test_cajero_con_items_calcula_total(self):
        c = self.login("cajaA@t.com")
        r = c.post("/api/comprobantes/", {"medio_pago": "efectivo", "items": [
            {"descripcion": "Menú", "cantidad": 2, "precio_unitario": "1500.50"},
            {"descripcion": "Agua", "cantidad": 1, "precio_unitario": "800"}]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        d = r.json()
        self.assertEqual(d["monto_total"], "3801.00")
        self.assertEqual(d["caja"], self.cajaA.pk)
        self.assertEqual(d["sede"], self.sedeA.pk)
        self.assertEqual(d["usuario"], self.cajeroA.pk)
        self.assertEqual(len(d["items"]), 2)
        self.assertEqual(d["items"][0]["subtotal"], "3001.00")

    def test_solo_monto_total(self):
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "1500"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["items"], [])

    def test_monto_no_coincide_con_items(self):
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "10",
            "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "5"}]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("monto_total", r.json())

    def test_monto_coincide_con_items_ok(self):
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "5.00",
            "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "5"}]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)

    def test_validaciones(self):
        c = self.login("cajaA@t.com")
        for body in (
            {"medio_pago": "efectivo"},                                   # sin monto ni items
            {"medio_pago": "efectivo", "monto_total": "0"},
            {"medio_pago": "efectivo", "monto_total": "-5"},
            {"medio_pago": "cheque", "monto_total": "5"},
            {"monto_total": "5"},
            {"medio_pago": "efectivo", "monto_total": "99999999999"},
            {"medio_pago": "efectivo", "items": [{"descripcion": "x", "cantidad": 0, "precio_unitario": "5"}]},
            {"medio_pago": "efectivo", "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "-1"}]},
            {"medio_pago": "efectivo", "items": [{"descripcion": "x", "cantidad": 1, "precio_unitario": "0"}]},
            {"medio_pago": "efectivo", "items": [{"cantidad": 1, "precio_unitario": "5"}]},
        ):
            r = c.post("/api/comprobantes/", body, format="json")
            self.assertEqual(r.status_code, 400, (body, r.content))
        self.assertEqual(Comprobante.objects.count(), 0)

    def test_caja_cerrada_o_inexistente(self):
        self.login("cajaA@t.com").post(f"/api/cajas/{self.cajaA.pk}/cerrar/")
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "5"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("caja", r.json())
        # admin indicando una caja cerrada
        r = self.login("admin@t.com").post("/api/comprobantes/", {"caja": self.cajaA.pk, "medio_pago": "qr", "monto_total": "5"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_cajero_no_puede_usar_caja_ajena_ni_sin_sede(self):
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"caja": self.cajaB.pk, "medio_pago": "qr", "monto_total": "5"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.login("sinsede@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "5"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_admin_indica_caja(self):
        c = self.login("admin@t.com")
        r = c.post("/api/comprobantes/", {"medio_pago": "tarjeta", "monto_total": "50"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = c.post("/api/comprobantes/", {"caja": self.cajaB.pk, "medio_pago": "tarjeta", "monto_total": "50"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["sede"], self.sedeB.pk)
        self.assertEqual(r.json()["usuario"], self.admin.pk)

    def test_campos_de_solo_lectura_se_ignoran(self):
        r = self.login("cajaA@t.com").post("/api/comprobantes/", {"medio_pago": "qr", "monto_total": "5",
            "sede": self.sedeB.pk, "usuario": self.admin.pk, "fecha": "2000-01-01T00:00:00Z"}, format="json")
        self.assertEqual(r.status_code, 201)
        d = r.json()
        self.assertEqual(d["sede"], self.sedeA.pk)
        self.assertEqual(d["usuario"], self.cajeroA.pk)
        self.assertNotEqual(d["fecha"][:4], "2000")

    def test_permisos(self):
        self.assertEqual(cliente().get("/api/comprobantes/").status_code, 401)
        self.assertEqual(self.login("compras@t.com").get("/api/comprobantes/").status_code, 403)
        self.assertEqual(self.login("compras@t.com").post("/api/comprobantes/", {}, format="json").status_code, 403)

    def test_sin_modificar_ni_borrar(self):
        c = self.login("admin@t.com")
        r = c.post("/api/comprobantes/", {"caja": self.cajaA.pk, "medio_pago": "qr", "monto_total": "5"}, format="json")
        pk = r.json()["id"]
        self.assertEqual(c.put(f"/api/comprobantes/{pk}/", {}, format="json").status_code, 405)
        self.assertEqual(c.patch(f"/api/comprobantes/{pk}/", {}, format="json").status_code, 405)
        self.assertEqual(c.delete(f"/api/comprobantes/{pk}/").status_code, 405)

    def _cargar(self):
        ahora = timezone.now()
        datos = [(self.cajaA, self.sedeA, self.cajeroA, "efectivo", "100", 0),
                 (self.cajaA, self.sedeA, self.cajeroA, "qr", "200", 3),
                 (self.cajaB, self.sedeB, self.cajeroB, "efectivo", "300", 10)]
        for caja, sede, u, medio, monto, dias in datos:
            Comprobante.objects.create(caja=caja, sede=sede, usuario=u, medio_pago=medio,
                                       monto_total=Decimal(monto), fecha=ahora - timedelta(days=dias))
        return ahora

    def test_visibilidad_y_filtros(self):
        ahora = self._cargar()
        a = self.login("cajaA@t.com")
        self.assertEqual(a.get("/api/comprobantes/").json()["count"], 2)
        self.assertEqual(a.get(f"/api/comprobantes/?sede={self.sedeB.pk}").json()["count"], 0)  # no ve otras sedes
        adm = self.login("admin@t.com")
        self.assertEqual(adm.get("/api/comprobantes/").json()["count"], 3)
        self.assertEqual(adm.get(f"/api/comprobantes/?sede={self.sedeB.pk}").json()["count"], 1)
        self.assertEqual(adm.get("/api/comprobantes/?medio_pago=efectivo").json()["count"], 2)
        self.assertEqual(adm.get(f"/api/comprobantes/?caja={self.cajaA.pk}").json()["count"], 2)
        h = timezone.localtime(ahora).date()
        d5 = (h - timedelta(days=5)).isoformat()
        self.assertEqual(adm.get(f"/api/comprobantes/?desde={d5}").json()["count"], 2)
        self.assertEqual(adm.get(f"/api/comprobantes/?hasta={d5}").json()["count"], 1)
        self.assertEqual(adm.get(f"/api/comprobantes/?desde={d5}&hasta={h.isoformat()}&sede={self.sedeA.pk}").json()["count"], 2)
        self.assertEqual(adm.get(f"/api/comprobantes/?desde={h.isoformat()}&hasta={h.isoformat()}").json()["count"], 1)
        # orden: más nuevo primero
        ids = [x["monto_total"] for x in adm.get("/api/comprobantes/").json()["results"]]
        self.assertEqual(ids, ["100.00", "200.00", "300.00"])

    def test_fechas_invalidas(self):
        c = self.login("admin@t.com")
        for q in ("desde=hoy", "hasta=2026-02-31", "desde=2026-05-02&hasta=2026-05-01"):
            self.assertEqual(c.get("/api/comprobantes/?" + q).status_code, 400, q)

    def test_detalle_y_aislamiento(self):
        self._cargar()
        b = Comprobante.objects.get(monto_total=300)
        self.assertEqual(self.login("cajaA@t.com").get(f"/api/comprobantes/{b.pk}/").status_code, 404)
        r = self.login("cajaB@t.com").get(f"/api/comprobantes/{b.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["sede_nombre"], "Norte")

    def test_totales_de_caja_usan_comprobantes(self):
        c = self.login("cajaA@t.com")
        c.post("/api/comprobantes/", {"medio_pago": "efectivo", "monto_total": "500"}, format="json")
        c.post("/api/comprobantes/", {"medio_pago": "efectivo", "monto_total": "250.50"}, format="json")
        c.post("/api/comprobantes/", {"medio_pago": "tarjeta", "monto_total": "1000"}, format="json")
        t = c.get(f"/api/cajas/{self.cajaA.pk}/totales/").json()
        self.assertEqual(t["cantidad_comprobantes"], 3)
        self.assertEqual(t["total_ventas"], "1750.50")
        self.assertEqual(t["efectivo_esperado"], "1750.50")  # 1000 apertura + 750.50 efectivo
        r = c.post(f"/api/cajas/{self.cajaA.pk}/cerrar/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["monto_cierre_calculado"], "1750.50")

    def test_restricciones_en_base(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comprobante.objects.create(caja=self.cajaA, sede=self.sedeA, usuario=self.cajeroA, medio_pago="qr", monto_total=0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Comprobante.objects.create(caja=self.cajaA, sede=self.sedeA, usuario=self.cajeroA, medio_pago="x", monto_total=5)

    def test_no_se_borra_caja_con_comprobantes(self):
        Comprobante.objects.create(caja=self.cajaA, sede=self.sedeA, usuario=self.cajeroA, medio_pago="qr", monto_total=5)
        from django.db.models import ProtectedError
        with self.assertRaises(ProtectedError):
            self.cajaA.delete()
