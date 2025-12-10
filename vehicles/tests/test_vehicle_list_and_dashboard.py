import pytest
from unittest.mock import patch
from vehicles.views import VehicleViewSet
from vehicles.models import Vehicle, VehicleStatusHistory

@pytest.mark.django_db
def test_vehicle_list_with_mocked_pilot(client, monkeypatch):
    # mock pilot_request_sync used in VehicleViewSet.list
    fake_data = {
        "list": [
            {"veh_id": 1, "imei": "i1", "vehiclenumber": "A", "type": "Truck",
             "status": {"lat": "42.0", "lon": "74.0"}, "sensors_status": [{"name": "топливо", "dig_value": "55"}]}
        ]
    }

    monkeypatch.setattr("vehicles.views.pilot_request_sync", lambda *a, **kw: fake_data)

    r = client.get("/api/vehicles/")
    assert r.status_code == 200
    data = r.json()
    assert data[0]["id"] == 1
    assert data[0]["fuel"] == 55.0

@pytest.mark.django_db
def test_dashboard_stats(client):
    v = Vehicle.objects.create(veh_id=10, imei="iiii", name="T10", fuel=10)
    VehicleStatusHistory.objects.create(vehicle=v, ts=1, lat=0, lon=0, ignition=True)
    r = client.get("/api/vehicles/dashboard/")
    assert r.status_code == 200
    j = r.json()
    assert j["stats"]["count_low_fuel"] >= 1
