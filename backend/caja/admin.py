from django.contrib import admin

from .models import Caja


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sede",
        "usuario",
        "estado",
        "fecha_apertura",
        "fecha_cierre",
        "monto_apertura",
        "monto_cierre_calculado",
    )
    list_filter = ("estado", "sede")
    search_fields = ("sede__nombre", "usuario__nombre", "usuario__email")
    list_select_related = ("sede", "usuario")
    date_hierarchy = "fecha_apertura"
    readonly_fields = ("monto_cierre_calculado",)
