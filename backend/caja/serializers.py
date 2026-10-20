from rest_framework import serializers

from .models import Caja
from .services import totales_para_api


class CajaSerializer(serializers.ModelSerializer):
    """Datos de una caja (listado y apertura)."""

    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.nombre", read_only=True)
    monto_apertura = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )

    class Meta:
        model = Caja
        fields = [
            "id",
            "sede",
            "sede_nombre",
            "usuario",
            "usuario_nombre",
            "fecha_apertura",
            "fecha_cierre",
            "monto_apertura",
            "monto_cierre_calculado",
            "estado",
        ]
        read_only_fields = [
            "id",
            "usuario",
            "fecha_apertura",
            "fecha_cierre",
            "monto_cierre_calculado",
            "estado",
        ]
        extra_kwargs = {"sede": {"required": False}}
        # DRF generaría un validador a partir de la restricción "una caja abierta por sede"
        # y exigiría la sede en el pedido. Esa regla se valida en validate(), con un mensaje claro.
        validators = []

    def validate(self, datos):
        usuario = self.context["request"].user
        sede = datos.get("sede")

        if usuario.rol == "cajero":
            if usuario.sede is None:
                raise serializers.ValidationError("Tu usuario no tiene una sede asignada.")
            if sede is not None and sede.pk != usuario.sede_id:
                raise serializers.ValidationError(
                    {"sede": "Un cajero solo puede abrir la caja de su sede."}
                )
            sede = usuario.sede
        elif sede is None:
            raise serializers.ValidationError({"sede": "La sede es obligatoria."})

        if not sede.activa:
            raise serializers.ValidationError(
                {"sede": "No se puede abrir una caja en una sede dada de baja."}
            )
        if Caja.objects.filter(sede=sede, estado=Caja.Estado.ABIERTA).exists():
            raise serializers.ValidationError("Ya hay una caja abierta en esta sede.")

        datos["sede"] = sede
        return datos


class CajaDetalleSerializer(CajaSerializer):
    """Igual que CajaSerializer, más el resumen de ventas (totales) de la caja."""

    totales = serializers.SerializerMethodField()

    class Meta(CajaSerializer.Meta):
        fields = CajaSerializer.Meta.fields + ["totales"]
        read_only_fields = CajaSerializer.Meta.read_only_fields + ["totales"]

    def get_totales(self, caja):
        return totales_para_api(caja)
