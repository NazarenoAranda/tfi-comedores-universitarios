from django.contrib import admin

from .models import Comprobante, ItemComprobante


class ItemComprobanteInline(admin.TabularInline):
    model = ItemComprobante
    extra = 0


@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "sede", "caja", "usuario", "medio_pago", "monto_total")
    list_filter = ("sede", "medio_pago")
    search_fields = ("id", "usuario__nombre", "usuario__email", "items__descripcion")
    list_select_related = ("sede", "caja", "usuario")
    date_hierarchy = "fecha"
    inlines = [ItemComprobanteInline]
