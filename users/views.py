from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView
from .models import VehicleRequest
from .serializers import (
    RegisterSerializer,
    LoginSerializers,
    LogoutSerializer,
    UserSerializer,
    FullUserRegisterSerializer
)
from django.contrib.auth import get_user_model

from vehicles.models import Vehicle, VehicleAssignment
from django.utils import timezone

User = get_user_model()


# ====================
# REGISTER
# ====================
class CustomRegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

# ====================
# LOGIN
# ====================
class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializers

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Неверные учетные данные"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


# ====================
# LOGIN FOR ADMINS ONLY
# ====================
class CustomAdminLoginView(TokenObtainPairView):
    serializer_class = LoginSerializers

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, 401)

        user = serializer.validated_data["user"]

        if not (user.is_staff or user.is_superuser):
            return Response(
                {"detail": "Доступ разрешен только администраторам"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(serializer.data, status=status.HTTP_200_OK)


# ====================
# LOGOUT
# ====================
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(
            {"detail": "Вы вышли из системы."},
            status=status.HTTP_205_RESET_CONTENT
        )


# ====================
# ME
# ====================
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "role": request.user.role,
            "email": request.user.email,
        })

# =======================
# TELEGRAM FULL REGISTER
# =======================
# users/views.py
class FullRegisterView(APIView):
    def post(self, request):
        data = request.data

        # --- Обязательные только те поля, что реально приходят из бота ---
        required = [
            "telegram_id", "name", "surname", "birthdate",
            "phone", "passport_id", "iin", "address",
            "passport_front", "passport_back",
            "driver_license", "selfie",
            "language", "vehicle_id"
        ]

        missing = [f for f in required if f not in data]
        if missing:
            return Response({"error": f"missing fields: {missing}"}, status=400)

        telegram_id = data["telegram_id"]

        # --- Если юзер уже существует, обновляем, иначе создаём ---
        try:
            user = User.objects.get(telegram_id=telegram_id)
            creating = False
        except User.DoesNotExist:
            user = User(telegram_id=telegram_id)
            creating = True

        # --- username и password обязательно нужны Django, но мы ставим безопасные дефолты ---
        if creating:
            user.username = f"user_{telegram_id}"
            user.set_password("default_password")

        # --- записываем все поля, которые реально пришли ---
        user.first_name = data["name"]
        user.surname = data["surname"]
        user.birthdate = data["birthdate"]
        user.phone = data["phone"]
        user.passport_id = data["passport_id"]
        user.iin = data["iin"]
        user.address = data["address"]
        user.passport_front = data["passport_front"]
        user.passport_back = data["passport_back"]
        user.driver_license = data["driver_license"]
        user.selfie = data["selfie"]
        user.language = data["language"]
        user.role = "driver"
        user.status = "pending_vehicle"

        user.save()

        # --- создаём заявку на технику ---
        req = VehicleRequest.objects.create(
            user=user,
            vehicle_id=data["vehicle_id"],
            status="pending"
        )

        return Response({
            "status": "ok",
            "user_id": user.id,
            "vehicle_request_id": req.id
        })


# =======================
# Telegram choose vehicle
# =======================
class VehicleRequestView(APIView):
    def post(self, request):
        tg = request.data.get("telegram_id")
        veh = request.data.get("vehicle_id")

        if not tg or not veh:
            return Response({"error": "telegram_id and vehicle_id required"}, 400)

        try:
            user = User.objects.get(telegram_id=tg)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, 404)

        req = VehicleRequest.objects.create(user=user, vehicle_id=veh)
        user.status = "pending_vehicle"
        user.save()

        return Response({"status": "ok", "request_id": req.id})


class UserProfileView(APIView):
    def get(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "not_found"}, 404)

        data = UserSerializer(user).data

        if user.status == "active":
            req = VehicleRequest.objects.filter(
                user=user, status="approved"
            ).last()
            data["vehicle_id"] = req.vehicle_id if req else None

        return Response(data)


class ApproveVehicleView(APIView):
    def post(self, request):
        tg = request.data.get("telegram_id")
        veh = request.data.get("vehicle_id")

        if not tg or not veh:
            return Response({"error": "telegram_id and vehicle_id required"}, 400)

        try:
            user = User.objects.get(telegram_id=tg)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, 404)

        req = VehicleRequest.objects.filter(user=user, vehicle_id=veh).last()
        if not req:
            return Response({"error": "vehicle_request_not_found"}, 404)

        req.status = "approved"
        req.save()

        user.status = "active"
        user.save()

        return Response({"status": "ok"})



class AssignVehicleView(APIView):
    def post(self, request):
        # ожидаем: { "telegram_id": 12345, "vehicle_id": 3881 }
        telegram_id = request.data.get("telegram_id")
        vehicle_id = request.data.get("vehicle_id")
        if not telegram_id or not vehicle_id:
            return Response({"error": "telegram_id and vehicle_id required"}, status=400)
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, status=404)
        try:
            vehicle = Vehicle.objects.get(veh_id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({"error": "vehicle_not_found"}, status=404)

        # снимаем предыдущие активные назначение для этого водителя или для этой машины (бизнес-логика)
        VehicleAssignment.objects.filter(vehicle=vehicle, unassigned_at__isnull=True).update(unassigned_at=timezone.now())
        # создаём новое назначение
        assign = VehicleAssignment.objects.create(vehicle=vehicle, driver=user)
        return Response({"status": "ok", "assignment_id": assign.id})
