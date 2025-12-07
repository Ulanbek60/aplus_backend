from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import VehicleRequest
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default="driver")

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializers(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data["username"],
            password=data["password"]
        )

        if user and user.is_active:
            return {"user": user}

        raise serializers.ValidationError("Неверные учетные данные")

    def to_representation(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Недействительный или уже отозванный токен"}
            )


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
