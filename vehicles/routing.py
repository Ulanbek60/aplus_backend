# vehicles/routing.py
from django.urls import re_path
from .consumers import VehicleStatusConsumer

websocket_urlpatterns = [
    # Глобальная группа: frontend может подключиться сюда и слушать все обновления
    re_path(r"ws/vehicles/$", VehicleStatusConsumer.as_asgi()),

    # Per-vehicle: frontend при открытии страницы машины подключается сюда, чтобы получать только её обновления
    re_path(r"ws/vehicles/(?P<vehicle_id>\d+)/$", VehicleStatusConsumer.as_asgi()),
]
