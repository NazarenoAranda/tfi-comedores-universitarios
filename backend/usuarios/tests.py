"""Pruebas automáticas de autenticación y de gestión de usuarios (API y panel de administración)."""
from django.db import IntegrityError, transaction  # noqa: F401  (se usa en las pruebas de restricciones)
from rest_framework.test import APIClient

from caja.models import Caja
from config.pruebas import PW, BaseApi, cliente
from usuarios.models import Usuario


class AuthTests(BaseApi):
    def test_login_ok_y_datos(self):
        r = APIClient().post("/api/auth/login/", {"email": "cajaA@t.com", "password": PW}, format="json")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d["usuario"]["rol"], "cajero")
        self.assertEqual(d["usuario"]["sede"], self.sedeA.pk)
        self.assertEqual(d["usuario"]["sede_nombre"], "Central")
        self.assertNotIn("password", d["usuario"])
        self.assertEqual(len(d["token"]), 40)

    def test_login_email_sin_distinguir_mayusculas_y_mismo_token(self):
        r1 = APIClient().post("/api/auth/login/", {"email": "CAJAA@T.COM", "password": PW}, format="json")
        r2 = APIClient().post("/api/auth/login/", {"email": " cajaa@t.com ", "password": PW}, format="json")
        self.assertEqual(r1.status_code, 200); self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.json()["token"], r2.json()["token"])

    def test_login_errores_mismo_mensaje(self):
        self.compras.is_active = False; self.compras.save()
        msgs = set()
        for email, pw in (("cajaA@t.com", "mala"), ("nadie@t.com", PW), ("compras@t.com", PW)):
            r = APIClient().post("/api/auth/login/", {"email": email, "password": pw}, format="json")
            self.assertEqual(r.status_code, 400)
            msgs.add(str(r.json()))
        self.assertEqual(len(msgs), 1)
        r = APIClient().post("/api/auth/login/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_me_logout(self):
        c = self.login("cajaA@t.com")
        self.assertEqual(c.get("/api/auth/me/").json()["email"], "cajaa@t.com")
        self.assertEqual(cliente().get("/api/auth/me/").status_code, 401)
        self.assertEqual(cliente("0" * 40).get("/api/auth/me/").status_code, 401)
        self.assertEqual(c.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(c.get("/api/auth/me/").status_code, 401)

    def test_health_publico(self):
        self.assertEqual(cliente().get("/api/health/").status_code, 200)


class UsuariosTests(BaseApi):
    def test_solo_admin(self):
        self.assertEqual(cliente().get("/api/usuarios/").status_code, 401)
        self.assertEqual(self.login("cajaA@t.com").get("/api/usuarios/").status_code, 403)
        self.assertEqual(self.login("compras@t.com").post("/api/usuarios/", {}, format="json").status_code, 403)
        r = self.login("admin@t.com").get("/api/usuarios/")
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json()["count"], 4)

    def test_alta_reglas(self):
        a = self.login("admin@t.com")
        base = {"nombre": "Nuevo", "email": "Nuevo@T.com", "password": "Otra-clave-456", "rol": "cajero"}
        r = a.post("/api/usuarios/", base, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("sede", r.json())          # cajero sin sede
        r = a.post("/api/usuarios/", {**base, "sede": self.sedeB.pk}, format="json")
        self.assertEqual(r.status_code, 201, r.content); self.assertNotIn("password", r.json())
        self.assertEqual(r.json()["email"], "nuevo@t.com")
        self.login("nuevo@t.com", "Otra-clave-456")                                    # puede iniciar sesión
        r = a.post("/api/usuarios/", {**base, "email": "NUEVO@t.com", "sede": self.sedeB.pk}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("email", r.json())         # duplicado
        r = a.post("/api/usuarios/", {**base, "email": "x@t.com", "password": "123", "sede": self.sedeB.pk}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("password", r.json())      # contraseña débil
        r = a.post("/api/usuarios/", {"nombre": "X", "email": "y@t.com", "rol": "compras"}, format="json")
        self.assertEqual(r.status_code, 400); self.assertIn("password", r.json())      # sin contraseña
        r = a.post("/api/usuarios/", {"nombre": "Comp", "email": "z@t.com", "password": "Otra-clave-456", "rol": "compras"}, format="json")
        self.assertEqual(r.status_code, 201); self.assertIsNone(r.json()["sede"])      # compras sin sede ok

    def test_modificar_cierra_sesiones_y_valida(self):
        a = self.login("admin@t.com")
        cajero = self.login("cajaA@t.com")
        r = a.patch(f"/api/usuarios/{self.cajeroA.pk}/", {"nombre": "Otro nombre"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cajero.get("/api/auth/me/").status_code, 200)                 # cambiar nombre no cierra sesión
        r = a.patch(f"/api/usuarios/{self.cajeroA.pk}/", {"password": "Nueva-clave-789"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cajero.get("/api/auth/me/").status_code, 401)                 # cambiar clave sí
        self.login("cajaA@t.com", "Nueva-clave-789")
        r = a.patch(f"/api/usuarios/{self.compras.pk}/", {"rol": "cajero"}, format="json")
        self.assertEqual(r.status_code, 400)                                           # pasa a cajero sin sede
        r = a.patch(f"/api/usuarios/{self.compras.pk}/", {"rol": "cajero", "sede": self.sedeA.pk}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_baja_logica(self):
        a = self.login("admin@t.com")
        b = self.login("cajaB@t.com")
        self.assertEqual(a.delete(f"/api/usuarios/{self.cajeroB.pk}/").status_code, 204)
        self.cajeroB.refresh_from_db(); self.assertFalse(self.cajeroB.is_active)
        self.assertEqual(b.get("/api/auth/me/").status_code, 401)
        r = APIClient().post("/api/auth/login/", {"email": "cajaB@t.com", "password": PW}, format="json")
        self.assertEqual(r.status_code, 400)
        r = a.delete(f"/api/usuarios/{self.admin.pk}/")
        self.assertEqual(r.status_code, 400)                                           # no se da de baja a sí mismo
        self.assertEqual(Usuario.objects.count(), 4)

    def test_filtros(self):
        a = self.login("admin@t.com")
        self.assertEqual(a.get("/api/usuarios/?rol=cajero").json()["count"], 2)
        self.assertEqual(a.get(f"/api/usuarios/?sede={self.sedeA.pk}").json()["count"], 1)
        self.assertEqual(a.get("/api/usuarios/?search=compras").json()["count"], 1)
        self.assertEqual(a.get("/api/usuarios/?activo=false").json()["count"], 0)


class AdminTests(BaseApi):
    def test_admin_django(self):
        from django.test import Client
        d = Client(); self.assertTrue(d.login(email="admin@t.com", password=PW))
        Caja.objects.create(sede=self.sedeA, usuario=self.cajeroA)
        for url in ("/admin/", "/admin/usuarios/usuario/", "/admin/usuarios/usuario/add/",
                    f"/admin/usuarios/usuario/{self.cajeroA.pk}/change/", "/admin/sedes/sede/", "/admin/caja/caja/", "/admin/ventas/comprobante/", f"/admin/caja/caja/{Caja.objects.first().pk}/change/"):
            self.assertEqual(d.get(url).status_code, 200, url)
        r = d.post("/admin/usuarios/usuario/add/", {"email": "nuevo@t.com", "nombre": "N", "rol": "cajero", "sede": self.sedeA.pk,
                                                    "password1": "Otra-clave-456", "password2": "Otra-clave-456"})
        self.assertEqual(r.status_code, 302)
        r = d.post("/admin/usuarios/usuario/add/", {"email": "n2@t.com", "nombre": "N", "rol": "cajero",
                                                    "password1": "Otra-clave-456", "password2": "Otra-clave-456"})
        self.assertEqual(r.status_code, 200)                                           # cajero sin sede: el formulario lo rechaza
        self.assertFalse(Usuario.objects.filter(email="n2@t.com").exists())
