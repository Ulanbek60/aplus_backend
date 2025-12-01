from django.urls import path
from .views import VehicleListView

urlpatterns = [
    path("list/", VehicleListView.as_view()),
]
