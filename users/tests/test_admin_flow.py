import pytest
from users.models import CustomUser, VehicleRequest
from vehicles.models import Vehicle, VehicleAssignment


@pytest.mark.django_db
def test_request_and_approve(client):
    # Создаём машину
    v = Vehicle.objects.create(veh_id=123, imei="imei123", name="Truck 1")

    # Full registration (бот регает юзера + создаёт заявку)
    resp = client.post(
        "/api/users/full_register/",
        {
            "telegram_id": 9999,
            "name": "John",
            "surname": "Doe",
            "birthdate": "1990-05-15",
            "phone": "+996000000000",
            "passport_id": "ID123",
            "iin": "12345678901234",
            "address": "Somewhere",
            "passport_front": "f1",
            "passport_back": "f2",
            "driver_license": "f3",
            "selfie": "f4",
            "language": "ru",
            "vehicle_id": v.veh_id
        },
        content_type="application/json"
    )

    assert resp.status_code == 200
    data = resp.json()

    user = CustomUser.objects.get(telegram_id=9999)
    req = VehicleRequest.objects.get(user=user)

    assert req.status == "pending"

    # 2) Админ утверждает заявку
    resp2 = client.post(
        "/api/users/approve_vehicle/",
        {"telegram_id": user.telegram_id, "vehicle_id": v.veh_id},
        content_type="application/json"
    )

    assert resp2.status_code == 200

    req.refresh_from_db()
    user.refresh_from_db()

    assert req.status == "approved"
    assert user.status == "active"

    # Проверяем VehicleAssignment
    assignment = VehicleAssignment.objects.filter(driver=user).last()
    assert assignment is not None
    assert assignment.vehicle.veh_id == v.veh_id


@pytest.mark.django_db
def test_assign_vehicle_creates_assignment(client):
    user = CustomUser.objects.create(
        username="u2",
        telegram_id=1111,
        email="u2@example.com",
        role="driver",
        status="registration"  # либо как у тебя логично
    )
    v = Vehicle.objects.create(veh_id=444, imei="im444", name="Truck444")

    # создаём pending заявку — важный шаг
    VehicleRequest.objects.create(user=user, vehicle_id=v.veh_id, status="pending")

    resp = client.post(
        "/api/users/approve_vehicle/",
        {"telegram_id": user.telegram_id, "vehicle_id": v.veh_id},
        content_type="application/json"
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"

    # Проверяем, что VehicleAssignment создан (имя модели у тебя — VehicleAssignment)
    from vehicles.models import VehicleAssignment
    assert VehicleAssignment.objects.filter(driver=user, vehicle__veh_id=v.veh_id, unassigned_at__isnull=True).exists()
