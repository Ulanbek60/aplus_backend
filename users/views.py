from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    LoginSerializers,
    LogoutSerializer,
    UserSerializer,
    FullUserRegisterSerializer
)
from django.contrib.auth import get_user_model
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
class FullRegisterView(APIView):
    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        vehicle_id = request.data.get("vehicle_id")

        if not telegram_id or not vehicle_id:
            return Response({"error": "telegram_id and vehicle_id required"}, status=400)

        try:
            user = User.objects.get(telegram_id=telegram_id)
            serializer = FullUserRegisterSerializer(user, data=request.data, partial=True)
        except User.DoesNotExist:
            serializer = FullUserRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()
        user.status = "pending_vehicle"
        user.save()

        req = VehicleRequest.objects.create(
            user=user,
            vehicle_id=vehicle_id,
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
