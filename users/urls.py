from django.urls import path
from .views import (
    RegisterView, LoginView, MeView,
    FullRegisterView, VehicleRequestView,
    UserProfileView, ApproveVehicleView
)

urlpatterns = [
    # registration
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),

    # Telegram workflow
    path("full_register/", FullRegisterView.as_view()),
    path("request_vehicle/", VehicleRequestView.as_view()),
    path("profile/<int:telegram_id>/", UserProfileView.as_view()),
    path("approve_vehicle/", ApproveVehicleView.as_view()),
]
