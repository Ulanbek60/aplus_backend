from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import VehicleRequest
from vehicles.models import Vehicle, VehicleAssignment
from vehicles.serializers import VehicleDetailSerializer  # для вложенного драйвера/техники
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


User = get_user_model()

# Исправленный UserSerializer — добавляем first_name и surname и created_at
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "surname", "phone", "telegram_id",
            "role", "status", "language", "created_at"
        ]


class DriverListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    current_vehicle = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "telegram_id", "first_name", "surname", "full_name", "phone", "status", "current_vehicle"]

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.surname or ''}".strip()

    def get_current_vehicle(self, obj):
        # находим активное назначение
        assign = VehicleAssignment.objects.filter(driver=obj, unassigned_at__isnull=True).select_related("vehicle").first()
        if not assign:
            return None
        v = assign.vehicle
        return {"veh_id": v.veh_id, "name": v.name, "plate_number": v.plate_number}


class VehicleRequestListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = VehicleRequest
        fields = ["id", "user", "vehicle_id", "status", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    # frontend отправляет только эти поля
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default="driver")

    class Meta:
        model = User
        fields = ["email", "password", "role"]

    # ---- VALIDATION ----
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as err:
            raise serializers.ValidationError(err.messages)
        return value

    # ---- CREATE ----
    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        role = validated_data["role"]

        # генерируем username
        base = email.split("@")[0].replace(".", "_").replace("-", "_")
        username = f"user_{base}"

        # гарантируем уникальность
        i = 1
        original = username
        while User.objects.filter(username=username).exists():
            username = f"{original}_{i}"
            i += 1

        # создаём пользователя
        user = User(
            username=username,
            email=email,
            role=role,
        )
        user.set_password(password)
        user.save()

        return user


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data["email"].lower()
        password = data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Неверный email или пароль.")

        if not user.check_password(password):
            raise serializers.ValidationError("Неверный email или пароль.")

        return {"user": user}

    def to_representation(self, validated_data):
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
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



class FullUserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class VehicleRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleRequest
        fields = ["user", "vehicle_id", "status", "created_at"]
