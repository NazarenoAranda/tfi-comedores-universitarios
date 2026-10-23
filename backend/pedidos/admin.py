from django.contrib import admin

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha_pedido", "proveedor", "sede", "usuario", "estado", "monto_total")
    list_filter = ("estado", "sede", "proveedor")
    search_fields = ("id", "proveedor__nombre", "items__descripcion")
    list_select_related = ("proveedor", "sede", "usuario")
    date_hierarchy = "fecha_pedido"
    inlines = [ItemPedidoInline]
