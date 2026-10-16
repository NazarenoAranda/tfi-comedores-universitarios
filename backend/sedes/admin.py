from django.contrib import admin

from .models import Sede


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "universidad", "direccion", "activa")
    list_filter = ("activa", "universidad")
    search_fields = ("nombre", "universidad", "direccion")
