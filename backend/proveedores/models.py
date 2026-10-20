from django.db import models


class Proveedor(models.Model):
    """Proveedor externo de insumos y alimentos de la cadena."""

    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=150, blank=True)
    # Baja lógica: un proveedor dado de baja se conserva para no perder el historial de pedidos.
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "proveedor"
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
