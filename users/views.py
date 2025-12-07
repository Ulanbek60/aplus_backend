from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserRegisterSerializer,
    LoginSerializer,
    UserSerializer,
    FullUserRegisterSerializer
)
from .models import VehicleRequest

User = get_user_model()


# =======================
# JWT REGISTER
# =======================
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=201)


# =======================
# JWT LOGIN
# =======================
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


# =======================
# /me
# =======================
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


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
