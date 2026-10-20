from rest_framework.routers import SimpleRouter

from .views import CajaViewSet

router = SimpleRouter()
router.register("cajas", CajaViewSet, basename="caja")

urlpatterns = router.urls
