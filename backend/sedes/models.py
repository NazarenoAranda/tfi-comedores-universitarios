from django.db import models


class Sede(models.Model):
    """Cada comedor de la cadena. Es el eje que conecta usuarios, cajas, comprobantes y pedidos."""

    nombre = models.CharField(max_length=150)
    universidad = models.CharField(max_length=150, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    # Baja lógica: una sede dada de baja se conserva para no perder el historial.
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "sede"
        verbose_name = "sede"
        verbose_name_plural = "sedes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
