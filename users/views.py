from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from .models import VehicleRequest
from .serializers import (
    RegisterSerializer,
    EmailLoginSerializer,
    LogoutSerializer,
    UserSerializer,
    FullUserRegisterSerializer,
)
from vehicles.models import Vehicle, VehicleAssignment
from django.db.models import Q
from rest_framework.permissions import AllowAny


User = get_user_model()


# ===========================================
# AUTHENTICATION
# ===========================================




class CustomRegisterView(APIView):
    """
    Регистрация пользователя (НЕ Telegram).
    """

    @swagger_auto_schema(
        operation_summary="Регистрация пользователя (НЕ Telegram)",
        operation_description="""
Эндпоинт для обычной регистрации пользователя (не Telegram).

Фронт отправляет:
- email
- password
- role (driver / mechanic / admin)

Что делает бэкенд:
1. Приводит email → lowercase
2. Проверяет уникальность email
3. Проверяет корректность пароля через Django validators
4. Создаёт пользователя через ModelSerializer
5. Сразу выдаёт JWT-токены (автоматический логин)

Возвращает:
- id
- username (генерируется автоматически)
- email
- role
- access token
- refresh token
        """,
        tags=["Authentication"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, example="driver@example.com"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, example="Qwerty123!"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, example="driver"),
            },
            required=["email", "password"],
        ),
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "username": openapi.Schema(type=openapi.TYPE_STRING),
                            "email": openapi.Schema(type=openapi.TYPE_STRING),
                            "role": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                    "access": openapi.Schema(type=openapi.TYPE_STRING),
                    "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            400: "Ошибка валидации",
        }
    )
    def post(self, request):
        data = request.data.copy()
        email = data.get("email")

        # Приводим email к lowercase
        if email:
            data["email"] = email.strip().lower()

        serializer = RegisterSerializer(data=data)

        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаём пользователя
        user = serializer.save()

        # Создаём JWT токены
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
                "access": str(access),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CustomLoginView(APIView):
    @swagger_auto_schema(
        operation_summary="Авторизация по email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["email", "password"]
        ),
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        return Response(serializer.data)


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    @swagger_auto_schema(
        operation_summary="Выход из системы",
        operation_description="Отзывает refresh-токен (blacklist)",
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Вы вышли из системы."}, 205)


# ===========================================
# TELEGRAM FULL REGISTER
# ===========================================

class FullRegisterView(APIView):

    @swagger_auto_schema(
        operation_summary="Полная регистрация водителя (Telegram)",
        operation_description="""
Используется Telegram-ботом.  

Что делает:
1. Создаёт или обновляет пользователя.  
2. Устанавливает статус registration → pending_vehicle.  
3. Создаёт заявку (VehicleRequest).  

После этого админ через адм. панель подтверждает заявку.
        """,
        tags=["Telegram Registration"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "telegram_id", "name", "surname", "birthdate", "phone",
                "passport_id", "iin", "address",
                "passport_front", "passport_back",
                "driver_license", "selfie",
                "language", "vehicle_id"
            ],
        ),
    )
    def post(self, request):
        data = request.data

        # проверка обязательных
        required = [
            "telegram_id", "name", "surname", "birthdate",
            "phone", "passport_id", "iin", "address",
            "passport_front", "passport_back",
            "driver_license", "selfie",
            "language", "vehicle_id",
        ]

        missing = [f for f in required if f not in data]
        if missing:
            return Response({"error": f"missing fields: {missing}"}, 400)

        telegram_id = data["telegram_id"]

        # создаём или обновляем пользователя
        try:
            user = User.objects.get(telegram_id=telegram_id)
            creating = False
        except User.DoesNotExist:
            user = User(telegram_id=telegram_id)
            creating = True

        if creating:
            user.username = f"user_{telegram_id}"
            user.set_password("default_password")
        # если из бота email не приходит, генерируем фейковый
        user.email = f"{telegram_id}@tg.local"
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

        # создаём заявку
        req = VehicleRequest.objects.create(
            user=user,
            vehicle_id=data["vehicle_id"],
            status="pending"
        )

        return Response({
            "status": "ok",
            "user_id": user.id,
            "vehicle_request_id": req.id,
        })


# ===========================================
# USER PROFILE (TELEGRAM)
# ===========================================

class UserProfileView(APIView):

    @swagger_auto_schema(
        operation_summary="Профиль пользователя по Telegram ID",
        operation_description="""
Возвращает:
• имя  
• телефон  
• язык  
• статус  
• vehicle_id (если активен)  
        """,
        tags=["Users"]
    )
    def get(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "not_found"}, 404)

        data = UserSerializer(user).data

        if user.status == "active":
            req = VehicleRequest.objects.filter(user=user, status="approved").last()
            data["vehicle_id"] = req.vehicle_id if req else None

        return Response(data)


# ===========================================
# ADMIN — APPROVE VEHICLE
# ===========================================

class ApproveVehicleView(APIView):

    @swagger_auto_schema(
        operation_summary="Подтвердить заявку водителя (ADMIN)",
        operation_description="""
После подтверждения:
1. VehicleRequest → approved  
2. User.status → active  
3. VehicleAssignment создаётся автоматически (техника привязывается к водителю)  
        """,
        tags=["Admin Panel"],
    )
    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        vehicle_id = request.data.get("vehicle_id")

        if not telegram_id or not vehicle_id:
            return Response({"error": "telegram_id and vehicle_id required"}, 400)

        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "user_not_found"}, 404)

        try:
            req = VehicleRequest.objects.get(user=user, vehicle_id=vehicle_id, status="pending")
        except VehicleRequest.DoesNotExist:
            return Response({"error": "pending_request_not_found"}, 404)

        # подтверждаем заявку
        req.status = "approved"
        req.save()

        # активируем пользователя
        user.status = "active"
        user.save()

        # отключаем предыдущие назначения
        VehicleAssignment.objects.filter(driver=user, unassigned_at__isnull=True).update(
            unassigned_at=timezone.now()
        )

        # создаём новое назначение
        vehicle = Vehicle.objects.get(veh_id=vehicle_id)
        VehicleAssignment.objects.create(
            driver=user,
            vehicle=vehicle,
        )

        return Response({
            "status": "approved",
            "user_id": user.id,
            "vehicle_id": vehicle_id,
        })


# ===========================================
# ADMIN — DRIVERS LIST
# ===========================================

class DriversListView(APIView):

    @swagger_auto_schema(
        operation_summary="Список всех водителей",
        operation_description="""
Возвращает:
• полное имя  
• телефон  
• статус  
• vehicle_id (если привязан)  
        """,
        tags=["Admin Panel"]
    )
    def get(self, request):
        users = User.objects.filter(role="driver")

        result = []
        for u in users:
            req = VehicleRequest.objects.filter(user=u, status="approved").last()
            result.append({
                "id": u.id,
                "full_name": f"{u.first_name} {u.surname}",
                "phone": u.phone,
                "status": u.status,
                "vehicle_id": req.vehicle_id if req else None
            })

        return Response(result)


# ===========================================
# ADMIN — DRIVER DETAIL
# ===========================================

class DriverDetailView(APIView):

    @swagger_auto_schema(
        operation_summary="Детальная информация о водителе",
        operation_description="""
Показывает:
• имя  
• фамилию  
• телефон  
• статус  
• vehicle_id (если активен)  
        """,
        tags=["Admin Panel"]
    )
    def get(self, request, id):
        try:
            u = User.objects.get(id=id, role="driver")
        except User.DoesNotExist:
            return Response({"error": "not_found"}, 404)

        req = VehicleRequest.objects.filter(user=u, status="approved").last()

        return Response({
            "id": u.id,
            "full_name": f"{u.first_name} {u.surname}",
            "phone": u.phone,
            "status": u.status,
            "vehicle_id": req.vehicle_id if req else None
        })


# ===========================================
# ADMIN — ALL REQUESTS
# ===========================================

class VehicleRequestsListView(APIView):

    @swagger_auto_schema(
        operation_summary="Все заявки на технику",
        operation_description="""
Показывает полный список заявок водителей:
• кто отправил  
• какая техника выбрана  
• статус заявки  
        """,
        tags=["Admin Panel"]
    )
    def get(self, request):
        qs = VehicleRequest.objects.select_related("user").all()

        result = [{
            "request_id": r.id,
            "user_id": r.user.id,
            "full_name": f"{r.user.first_name} {r.user.surname}",
            "phone": r.user.phone,
            "vehicle_id": r.vehicle_id,
            "status": r.status,
            "created_at": r.created_at,
        } for r in qs]

        return Response(result)


# ===========================================
# ADMIN — ONLY PENDING REQUESTS
# ===========================================

class PendingRequestsView(APIView):

    @swagger_auto_schema(
        operation_summary="Заявки в статусе pending",
        operation_description="Список заявок, которые ждут подтверждения администратором.",
        tags=["Admin Panel"]
    )
    def get(self, request):
        qs = VehicleRequest.objects.filter(status="pending").select_related("user")

        result = [{
            "request_id": r.id,
            "user_id": r.user.id,
            "full_name": f"{r.user.first_name} {r.user.surname}",
            "phone": r.user.phone,
            "vehicle_id": r.vehicle_id,
            "created_at": r.created_at,
        } for r in qs]

        return Response(result)
