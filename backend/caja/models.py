from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Caja(models.Model):
    """Apertura y cierre de la caja de una sede. Agrupa los comprobantes de venta de ese período."""

    class Estado(models.TextChoices):
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    sede = models.ForeignKey("sedes.Sede", on_delete=models.PROTECT, related_name="cajas")
    # Cajero que abrió la caja.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cajas"
    )
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_apertura = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    # Efectivo que debería haber en la caja al cerrar (se calcula al cerrarla).
    monto_cierre_calculado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTA)

    class Meta:
        db_table = "caja"
        verbose_name = "caja"
        verbose_name_plural = "cajas"
        ordering = ["-fecha_apertura"]
        constraints = [
            # La base de datos garantiza que cada sede tenga como máximo una caja abierta.
            models.UniqueConstraint(
                fields=["sede"],
                condition=models.Q(estado="abierta"),
                name="una_caja_abierta_por_sede",
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=["abierta", "cerrada"]),
                name="caja_estado_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(monto_apertura__gte=0),
                name="caja_monto_apertura_no_negativo",
            ),
        ]

    def __str__(self):
        return f"Caja #{self.pk} — {self.sede} ({self.get_estado_display()})"
