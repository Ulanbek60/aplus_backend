# users/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, VehicleRequest
from .serializers import (
    FullUserRegisterSerializer,
    UserProfileSerializer
)


class FullRegisterView(APIView):
    def post(self, request):
        telegram_id = request.data.get("telegram_id")

        if not telegram_id:
            return Response({"error": "telegram_id required"}, status=400)

        # Проверяем, есть ли пользователь
        try:
            user = User.objects.get(telegram_id=telegram_id)
            serializer = FullUserRegisterSerializer(user, data=request.data, partial=True)
        except User.DoesNotExist:
            serializer = FullUserRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()

        # Логика ролей и статусов
        if user.role == "driver":
            user.status = "pending_vehicle"
            user.save()

            return Response({
                "status": "ok",
                "next": "pending_vehicle",
                "message": "Заявка отправлена. Ожидайте подтверждения техники администратором."
            })

        if user.role == "mechanic":
            user.status = "active"
            user.save()

            return Response({
                "status": "ok",
                "next": "active",
                "message": "Механик успешно зарегистрирован."
            })

        return Response({"status": "ok"})


class VehicleRequestView(APIView):
    def post(self, request):
        tg_id = request.data.get("telegram_id")
        veh_id = request.data.get("vehicle_id")

        if not tg_id or not veh_id:
            return Response({"error": "telegram_id and vehicle_id required"}, status=400)

        try:
            user = User.objects.get(telegram_id=tg_id)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, status=404)

        # Создаём заявку
        req = VehicleRequest.objects.create(
            user=user,
            vehicle_id=veh_id,
            status="pending"
        )

        # Меняем статус
        user.status = "pending_vehicle"
        user.save()

        return Response({
            "status": "ok",
            "request_id": req.id,
            "user_status": user.status
        })


class UserProfileView(APIView):
    def get(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, status=404)

        data = UserProfileSerializer(user).data

        # Если водитель активный — добавить vehicle_id
        if user.status == "active":
            req = VehicleRequest.objects.filter(
                user=user, status="approved"
            ).last()

            data["vehicle_id"] = req.vehicle_id if req else None

        return Response(data)


class ApproveVehicleView(APIView):
    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        vehicle_id = request.data.get("vehicle_id")

        if not telegram_id or not vehicle_id:
            return Response({"error": "telegram_id and vehicle_id required"}, status=400)

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, status=404)

        req = VehicleRequest.objects.filter(
            user=user,
            vehicle_id=vehicle_id
        ).last()

        if not req:
            return Response({"error": "vehicle_request_not_found"}, status=404)

        req.status = "approved"
        req.save()

        user.status = "active"
        user.save()

        return Response({
            "status": "ok",
            "message": "Vehicle approved and user activated."
        })
