from django.urls import path

from .views import ResumenView

urlpatterns = [
    path("dashboard/resumen/", ResumenView.as_view(), name="dashboard-resumen"),
]
