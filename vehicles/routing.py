from django.urls import re_path
from .consumers import VehicleStatusConsumer

websocket_urlpatterns = [
    re_path(r"ws/vehicles/$", VehicleStatusConsumer.as_asgi()),
]
