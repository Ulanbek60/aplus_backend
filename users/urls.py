from django.urls import path
from django.urls import path
from .views import (
    CustomRegisterView, CustomLoginView, CustomAdminLoginView, LogoutView, MeView,FullRegisterView, VehicleRequestView,
    UserProfileView, ApproveVehicleView, AssignVehicleView
)

urlpatterns = [
    # registration
    path("register/", CustomRegisterView.as_view()),
    path("login/", CustomLoginView.as_view()),
    path("me/", MeView.as_view()),
    path("admin_login/", CustomAdminLoginView.as_view()),
    path("logout/", LogoutView.as_view()),

    # Telegram workflow
    path("full_register/", FullRegisterView.as_view()),
    path("request_vehicle/", VehicleRequestView.as_view()),
    path("profile/<int:telegram_id>/", UserProfileView.as_view()),
    path("approve_vehicle/", ApproveVehicleView.as_view()),
    path("assign_vehicle/", AssignVehicleView.as_view()),
]
