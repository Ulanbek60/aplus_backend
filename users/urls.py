from django.urls import path
from .views import (
    FullRegisterView,
    VehicleRequestView,
    UserProfileView,
    ApproveVehicleView
)

urlpatterns = [
    path("full_register/", FullRegisterView.as_view()),     # новая полная регистрация
    path("request_vehicle/", VehicleRequestView.as_view()), # водитель выбирает технику
    path("approve_vehicle/", ApproveVehicleView.as_view()), # админ подтверждает технику
    path("profile/<int:telegram_id>/", UserProfileView.as_view()),
]
