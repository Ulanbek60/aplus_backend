from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import VehicleViewSet, DashboardStatsView, VehicleDetailView

router = SimpleRouter()
router.register(r"", VehicleViewSet, basename="vehicles")

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view()),
    path("<int:vehicle_id>/detail/", VehicleDetailView.as_view()),
]

urlpatterns += router.urls
