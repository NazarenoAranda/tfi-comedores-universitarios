from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Datos del usuario para mostrar (login, /auth/me/)."""

    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default=None)

    class Meta:
        model = Usuario
        fields = ["id", "nombre", "email", "rol", "sede", "sede_nombre", "is_active"]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, datos):
        usuario = authenticate(
            request=self.context.get("request"),
            email=datos["email"].strip(),
            password=datos["password"],
        )
        # Mismo mensaje si el email no existe, la clave es incorrecta o el usuario
        # está dado de baja: no se revela cuál de los casos es.
        if usuario is None:
            raise serializers.ValidationError("Email o contraseña incorrectos.")
        datos["usuario"] = usuario
        return datos


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Alta, modificación y consulta de usuarios por parte de la administración."""

    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default=None)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "nombre",
            "email",
            "password",
            "rol",
            "sede",
            "sede_nombre",
            "is_active",
            "fecha_creacion",
        ]
        read_only_fields = ["id", "fecha_creacion"]

    def validate_email(self, valor):
        valor = valor.strip().lower()
        repetidos = Usuario.objects.filter(email__iexact=valor)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return valor

    def validate_password(self, valor):
        validate_password(valor, user=self.instance)
        return valor

    def validate(self, datos):
        if self.instance is None and not datos.get("password"):
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})
        rol = datos.get("rol", self.instance.rol if self.instance else Usuario.Rol.CAJERO)
        if "sede" in datos:
            sede = datos["sede"]
        else:
            sede = self.instance.sede if self.instance else None
        if rol == Usuario.Rol.CAJERO and sede is None:
            raise serializers.ValidationError({"sede": "Un cajero debe tener una sede asignada."})
        return datos

    def create(self, datos):
        password = datos.pop("password")
        return Usuario.objects.create_user(password=password, **datos)

    def update(self, instancia, datos):
        password = datos.pop("password", None)
        for campo, valor in datos.items():
            setattr(instancia, campo, valor)
        if password:
            instancia.set_password(password)
        instancia.save()
        # Si cambia la contraseña o se da de baja, se cierran sus sesiones abiertas.
        if password or not instancia.is_active:
            Token.objects.filter(user=instancia).delete()
        return instancia
