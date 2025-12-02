from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, VehicleRequest
from .serializers import UserRegisterSerializer, UserProfileSerializer

class UserRegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            tg_id = serializer.validated_data['telegram_id']

            # если юзер уже есть — не создаём новый
            user, created = User.objects.update_or_create(
                telegram_id=tg_id,
                defaults=serializer.validated_data
            )
            return Response({
                "status": "ok",
                "user_id": user.id,
                "next_stage": user.status
            })

        return Response(serializer.errors, status=54)


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

        # Меняем статус пользователя
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

        # Если водитель активный — можем дать vehicle_id (через VehicleRequest)
        if user.status == "active":
            req = VehicleRequest.objects.filter(
                user=user, status="approved"
            ).last()

            data["vehicle_id"] = req.vehicle_id if req else None

        return Response(data)

