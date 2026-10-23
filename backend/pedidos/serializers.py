from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from proveedores.models import Proveedor
from sedes.models import Sede

from .models import ItemPedido, Pedido

MONTO_MAXIMO = Decimal("9999999999.99")  # lo que entra en NUMERIC(12,2)
MAX_ITEMS = 100


class ItemPedidoSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField(min_value=1, max_value=100000, default=1)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "descripcion", "cantidad", "precio_unitario", "subtotal"]
        read_only_fields = ["id"]


class PedidoSerializer(serializers.ModelSerializer):
    """Pedido a un proveedor. El monto total es la suma de cantidad x precio de los ítems."""

    proveedor = serializers.PrimaryKeyRelatedField(queryset=Proveedor.objects.all())
    sede = serializers.PrimaryKeyRelatedField(queryset=Sede.objects.all())
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    items = ItemPedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "proveedor",
            "proveedor_nombre",
            "sede",
            "sede_nombre",
            "usuario",
            "usuario_nombre",
            "fecha_pedido",
            "fecha_recibido",
            "estado",
            "monto_total",
            "items",
        ]
        read_only_fields = ["id", "usuario", "fecha_pedido", "fecha_recibido", "estado", "monto_total"]

    def validate_proveedor(self, proveedor):
        if not proveedor.activo:
            raise serializers.ValidationError("El proveedor está dado de baja.")
        return proveedor

    def validate_sede(self, sede):
        if not sede.activa:
            raise serializers.ValidationError("La sede está dada de baja.")
        return sede

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("El pedido necesita al menos un ítem.")
        if len(items) > MAX_ITEMS:
            raise serializers.ValidationError(f"Un pedido admite hasta {MAX_ITEMS} ítems.")
        return items

    def validate(self, datos):
        total = sum((i["cantidad"] * i["precio_unitario"] for i in datos["items"]), Decimal("0"))
        if total <= 0:
            raise serializers.ValidationError({"items": "La suma de los ítems tiene que ser mayor a cero."})
        if total > MONTO_MAXIMO:
            raise serializers.ValidationError({"items": "El monto del pedido es demasiado grande."})
        datos["monto_total"] = total
        return datos

    def create(self, datos):
        items = datos.pop("items")
        with transaction.atomic():
            pedido = Pedido.objects.create(usuario=self.context["request"].user, **datos)
            ItemPedido.objects.bulk_create([ItemPedido(pedido=pedido, **item) for item in items])
        return pedido
