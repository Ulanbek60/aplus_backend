from django.urls import path, include
from .views import UserRegisterView, VehicleRequestView

urlpatterns = [
    path("register/", UserRegisterView.as_view()),
    path("request_vehicle/", VehicleRequestView.as_view()),
]
