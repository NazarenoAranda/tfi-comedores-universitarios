from rest_framework.routers import SimpleRouter

from .views import SedeViewSet

router = SimpleRouter()
router.register("sedes", SedeViewSet, basename="sede")

urlpatterns = router.urls
