from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        # El login no distingue mayúsculas de minúsculas en el email.
        return self.get(email__iexact=email)

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El email es obligatorio.")
        usuario = self.model(email=self.normalize_email(email), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("rol", Usuario.Rol.ADMIN)
        return self._crear(email, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Persona que usa el sistema. Inicia sesión con su email."""

    class Rol(models.TextChoices):
        ADMIN = "admin", "Administración"
        CAJERO = "cajero", "Cajero"
        COMPRAS = "compras", "Encargado de compras"

    nombre = models.CharField(max_length=150)
    email = models.EmailField(max_length=150, unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CAJERO)
    # Sede a la que pertenece. Es obligatoria para los cajeros; la administración
    # y compras pueden no tener sede fija.
    sede = models.ForeignKey(
        "sedes.Sede",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
    )
    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField(
        "acceso al panel de administración", default=False
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    def clean(self):
        super().clean()
        self.email = (self.email or "").strip().lower()
        if self.rol == self.Rol.CAJERO and not self.sede_id:
            raise ValidationError({"sede": "Un cajero debe tener una sede asignada."})

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)
