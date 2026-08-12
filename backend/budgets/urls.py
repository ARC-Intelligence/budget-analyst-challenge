from rest_framework.routers import DefaultRouter

from .views import LineItemViewSet, ScenarioViewSet

router = DefaultRouter()
router.register("scenarios", ScenarioViewSet)
router.register("line-items", LineItemViewSet)

urlpatterns = router.urls
