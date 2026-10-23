from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from caja.models import Caja

from .models import Comprobante, ItemComprobante

MONTO_MAXIMO = Decimal("9999999999.99")  # lo que entra en NUMERIC(12,2)
MAX_ITEMS = 100


class ItemComprobanteSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField(min_value=1, max_value=100000, default=1)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ItemComprobante
        fields = ["id", "descripcion", "cantidad", "precio_unitario", "subtotal"]
        read_only_fields = ["id"]


class ComprobanteSerializer(serializers.ModelSerializer):
    """
    Una venta. Se puede cargar de dos formas:

    - con ítems: el monto total se calcula como la suma de cantidad x precio de cada ítem;
    - solo con el monto total (sin ítems).
    """

    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    caja = serializers.PrimaryKeyRelatedField(queryset=Caja.objects.all(), required=False)
    monto_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False
    )
    items = ItemComprobanteSerializer(many=True, required=False)

    class Meta:
        model = Comprobante
        fields = [
            "id",
            "caja",
            "sede",
            "sede_nombre",
            "usuario",
            "usuario_nombre",
            "fecha",
            "medio_pago",
            "monto_total",
            "items",
        ]
        read_only_fields = ["id", "sede", "usuario", "fecha"]

    def validate_items(self, items):
        if len(items) > MAX_ITEMS:
            raise serializers.ValidationError(f"Un comprobante admite hasta {MAX_ITEMS} ítems.")
        return items

    def validate(self, datos):
        usuario = self.context["request"].user
        caja = datos.get("caja")

        # --- Caja en la que se carga la venta ---------------------------------------------
        if usuario.rol == "cajero":
            if usuario.sede_id is None:
                raise serializers.ValidationError("Tu usuario no tiene una sede asignada.")
            if caja is None:
                caja = Caja.objects.filter(sede_id=usuario.sede_id, estado=Caja.Estado.ABIERTA).first()
                if caja is None:
                    raise serializers.ValidationError(
                        {"caja": "No hay una caja abierta en tu sede. Abrí la caja antes de cargar ventas."}
                    )
            elif caja.sede_id != usuario.sede_id:
                raise serializers.ValidationError({"caja": "La caja no pertenece a tu sede."})
        elif caja is None:
            raise serializers.ValidationError({"caja": "Indicá la caja en la que se carga la venta."})

        if caja.estado != Caja.Estado.ABIERTA:
            raise serializers.ValidationError(
                {"caja": "La caja está cerrada: no se pueden cargar ventas."}
            )
        datos["caja"] = caja

        # --- Monto total ------------------------------------------------------------------
        items = datos.get("items") or []
        if items:
            suma = sum((i["cantidad"] * i["precio_unitario"] for i in items), Decimal("0"))
            if suma <= 0:
                raise serializers.ValidationError({"items": "La suma de los ítems tiene que ser mayor a cero."})
            monto = datos.get("monto_total")
            if monto is not None and monto != suma:
                raise serializers.ValidationError(
                    {"monto_total": f"No coincide con la suma de los ítems ({suma:.2f}). "
                                    "Se puede omitir: se calcula solo."}
                )
            datos["monto_total"] = suma
        elif datos.get("monto_total") is None:
            raise serializers.ValidationError(
                {"monto_total": "Indicá el monto total o cargá los ítems de la venta."}
            )
        if datos["monto_total"] > MONTO_MAXIMO:
            raise serializers.ValidationError({"monto_total": "El monto es demasiado grande."})
        return datos

    def create(self, datos):
        items = datos.pop("items", [])
        caja = datos.pop("caja")
        with transaction.atomic():
            # Se bloquea la caja: si se está cerrando en este momento, la venta espera y se
            # rechaza, en lugar de quedar fuera del total del cierre.
            caja = Caja.objects.select_for_update().get(pk=caja.pk)
            if caja.estado != Caja.Estado.ABIERTA:
                raise serializers.ValidationError(
                    {"caja": "La caja está cerrada: no se pueden cargar ventas."}
                )
            comprobante = Comprobante.objects.create(
                caja=caja,
                sede=caja.sede,
                usuario=self.context["request"].user,
                **datos,
            )
            ItemComprobante.objects.bulk_create(
                [ItemComprobante(comprobante=comprobante, **item) for item in items]
            )
        return comprobante
