import pytest
from users.models import VehicleRequest, CustomUser
from vehicles.models import Vehicle, VehicleAssignment

@pytest.mark.django_db
def test_request_and_approve(client):
    # подготовка: создаём пользователя (существует в БД)
    user = CustomUser.objects.create(
        username="t1", telegram_id=9999, email="t1@example.com",
        role="driver", status="registration"
    )

    # создаём тестовую машину
    v = Vehicle.objects.create(veh_id=123, imei="imei123", name="Truck 1")

    # 1) запрос техники
    resp = client.post("/api/users/request_vehicle/", {"telegram_id": user.telegram_id, "vehicle_id": v.veh_id}, content_type="application/json")
    assert resp.status_code == 200
    assert VehicleRequest.objects.filter(user=user, vehicle_id=str(v.veh_id)).exists()

    # 2) админ подтверждает
    resp2 = client.post("/api/users/approve_vehicle/", {"telegram_id": user.telegram_id, "vehicle_id": v.veh_id}, content_type="application/json")
    assert resp2.status_code == 200

    user.refresh_from_db()
    assert user.status == "active"

@pytest.mark.django_db
def test_assign_vehicle_creates_assignment():
    user = CustomUser.objects.create(username="u2", telegram_id=1111, email="u2@example.com", role="driver", status="active")
    v = Vehicle.objects.create(veh_id=444, imei="im444", name="Truck444")

    # assign
    resp = client.post("/api/users/assign_vehicle/", {"telegram_id": user.telegram_id, "vehicle_id": v.veh_id}, content_type="application/json")
    assert resp.status_code == 200
    assert VehicleAssignment.objects.filter(vehicle=v, driver=user, unassigned_at__isnull=True).exists()
