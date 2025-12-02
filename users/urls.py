from django.urls import path, include
from .views import UserRegisterView, VehicleRequestView, UserProfileView

urlpatterns = [
    path("register/", UserRegisterView.as_view()),
    path("request_vehicle/", VehicleRequestView.as_view()),
    path("profile/<int:telegram_id>/", UserProfileView.as_view()),
]
