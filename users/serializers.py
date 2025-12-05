from .models import User, VehicleRequest

# users/serializers.py
from rest_framework import serializers
from .models import User

class FullUserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "telegram_id",
            "name",
            "surname",
            "birthdate",
            "phone",
            "passport_id",
            "iin",
            "address",
            "passport_front",
            "passport_back",
            "driver_license",
            "selfie",
            "language",
            "role",
        ]


class VehicleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleRequest
        fields = ['user', 'vehicle_id']




class UserProfileSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "telegram_id",
            "name",
            "surname",
            "birthdate",
            "phone",
            "language",

            "passport_id",
            "iin",
            "address",

            "passport_front",
            "passport_back",
            "driver_license",
            "selfie",

            "role",
            "status",
            "vehicle_id",
        ]

    def get_vehicle_id(self, obj):
        """Отдаём vehicle_id только если пользователь активный водитель."""

        if obj.role != "driver":
            return None

        if obj.status != "active":
            return None

        req = VehicleRequest.objects.filter(
            user=obj,
            status="approved"
        ).last()

        return req.vehicle_id if req else None
