"""URLs of the machines API."""

from rest_framework.routers import DefaultRouter

from .views import MachineViewSet

router = DefaultRouter()
router.register("machines", MachineViewSet)

urlpatterns = router.urls