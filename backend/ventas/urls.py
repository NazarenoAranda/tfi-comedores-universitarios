from rest_framework.routers import SimpleRouter

from .views import ComprobanteViewSet

router = SimpleRouter()
router.register("comprobantes", ComprobanteViewSet, basename="comprobante")

urlpatterns = router.urls
