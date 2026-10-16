from rest_framework import serializers

from .models import Sede


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = ["id", "nombre", "universidad", "direccion", "activa"]

    def validate_nombre(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return valor
