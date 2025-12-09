from django.urls import path
from .views import (
    CustomRegisterView, CustomLoginView, LogoutView,
    FullRegisterView, UserProfileView, ApproveVehicleView,
    DriversListView, DriverDetailView,
    VehicleRequestsListView, PendingRequestsView
)

urlpatterns = [
    # ============================
    # Authentication (Web)
    # ============================
    path("register/", CustomRegisterView.as_view()),      # обычная регистрация (не Telegram)
    path("login/", CustomLoginView.as_view()),            # JWT login
    path("logout/", LogoutView.as_view()),                # revoke refresh token

    # ============================
    # Telegram registration flow
    # ============================
    path("full_register/", FullRegisterView.as_view()),   # полная регистрация водителя
    path("profile/<int:telegram_id>/", UserProfileView.as_view()),  # данные для Telegram бота
    path("approve_vehicle/", ApproveVehicleView.as_view()),         # админ подтверждает технику

    # ============================
    # Admin panel (Frontend)
    # ============================
    path("drivers/", DriversListView.as_view()),                 # список водителей
    path("drivers/<int:id>/", DriverDetailView.as_view()),       # детальный профиль водителя
    path("vehicle_requests/", VehicleRequestsListView.as_view()),# все заявки
    path("requests/pending/", PendingRequestsView.as_view()),    # ожидающие заявки
    
]
