from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, DashboardStatsView

router = DefaultRouter()
router.register(r"", VehicleViewSet, basename="vehicles")

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view()),
]

urlpatterns += router.urls
