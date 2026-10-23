from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Pedido(models.Model):
    """Pedido de mercadería que una sede le hace a un proveedor."""

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        RECIBIDO = "recibido", "Recibido"
        CANCELADO = "cancelado", "Cancelado"

    proveedor = models.ForeignKey("proveedores.Proveedor", on_delete=models.PROTECT, related_name="pedidos")
    sede = models.ForeignKey("sedes.Sede", on_delete=models.PROTECT, related_name="pedidos")
    # Usuario (compras o administración) que registró el pedido.
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos")
    fecha_pedido = models.DateTimeField(default=timezone.now)
    fecha_recibido = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "pedido"
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-fecha_pedido", "-id"]
        indexes = [
            models.Index(fields=["proveedor"], name="idx_pedido_proveedor"),
            models.Index(fields=["sede", "estado"], name="idx_pedido_sede_estado"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estado__in=["pendiente", "recibido", "cancelado"]),
                name="pedido_estado_valido",
            ),
        ]

    def __str__(self):
        return f"Pedido #{self.pk} — {self.proveedor} — {self.get_estado_display()}"


class ItemPedido(models.Model):
    """Línea de un pedido: qué se pidió, cuánto y a qué precio."""

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    descripcion = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        db_table = "item_pedido"
        verbose_name = "ítem de pedido"
        verbose_name_plural = "ítems de pedido"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name="item_pedido_cantidad_valida"),
            models.CheckConstraint(
                condition=models.Q(precio_unitario__gte=0), name="item_pedido_precio_no_negativo"
            ),
        ]

    @property
    def subtotal(self):
        return (self.precio_unitario * self.cantidad).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.cantidad} x {self.descripcion}"
