from rest_framework import serializers
from .models import User, VehicleRequest


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['telegram_id', 'phone', 'name', 'surname', 'language']


class VehicleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleRequest
        fields = ['user', 'vehicle_id']
