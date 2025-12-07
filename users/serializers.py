from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import VehicleRequest

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "phone",
            "telegram_id",
            "surname",
            "language",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"),
            password=attrs.get("password")
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "phone", "telegram_id",
            "role", "status", "language"
        ]


class FullUserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class VehicleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleRequest
        fields = ["user", "vehicle_id", "status", "created_at"]
