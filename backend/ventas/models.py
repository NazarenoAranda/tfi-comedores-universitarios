from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Comprobante(models.Model):
    """Una venta registrada en la caja de una sede."""

    class MedioPago(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TARJETA = "tarjeta", "Tarjeta"
        TRANSFERENCIA = "transferencia", "Transferencia"
        QR = "qr", "QR"

    caja = models.ForeignKey("caja.Caja", on_delete=models.PROTECT, related_name="comprobantes")
    # La sede se guarda también acá (aunque se podría obtener desde la caja) para filtrar las
    # ventas por sede y fecha sin un JOIN extra: es la consulta más frecuente del sistema.
    sede = models.ForeignKey("sedes.Sede", on_delete=models.PROTECT, related_name="comprobantes")
    # Cajero (o administrador) que cargó la venta.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comprobantes"
    )
    fecha = models.DateTimeField(default=timezone.now)
    medio_pago = models.CharField(max_length=20, choices=MedioPago.choices)
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    class Meta:
        db_table = "comprobante"
        verbose_name = "comprobante"
        verbose_name_plural = "comprobantes"
        ordering = ["-fecha", "-id"]
        indexes = [models.Index(fields=["sede", "fecha"], name="idx_comprobante_sede_fecha")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(medio_pago__in=["efectivo", "tarjeta", "transferencia", "qr"]),
                name="comprobante_medio_pago_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(monto_total__gt=0),
                name="comprobante_monto_positivo",
            ),
        ]

    def __str__(self):
        return f"Comprobante #{self.pk} — {self.sede} — ${self.monto_total}"


class ItemComprobante(models.Model):
    """Detalle de lo vendido en un comprobante (opcional: se puede cargar solo el monto total)."""

    comprobante = models.ForeignKey(Comprobante, on_delete=models.CASCADE, related_name="items")
    descripcion = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        db_table = "item_comprobante"
        verbose_name = "ítem de comprobante"
        verbose_name_plural = "ítems de comprobante"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name="item_comprobante_cantidad_valida"),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0), name="item_comprobante_precio_no_negativo"
            ),
        ]

    @property
    def subtotal(self):
        return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.cantidad} x {self.descripcion}"
