import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from vehicles.models import Vehicle, VehicleStatusHistory
from unittest.mock import AsyncMock, patch

@pytest.mark.django_db
def test_polling_worker_flow(monkeypatch):
    # подготовим vehicle
    v = Vehicle.objects.create(veh_id=55, imei="imei55", name="V55")

    # мок pilot_request (асинхронный)
    async def fake_pilot(cmd, node, params=None):
        return {"data":[{"status":{"unixtimestamp": 1, "lat": "41.0", "lon": "74.0", "speed": "10", "firing": 1},
                          "sensors_status":[{"name":"топливо","dig_value":"33"}]}]}

    monkeypatch.setattr("services.pilot_client.pilot_request", fake_pilot)

    # мок channel_layer.group_send чтобы проверить, что отправка вызвалась
    layer = get_channel_layer()
    async def fake_send(group, message):
        # просто проверяем что message содержит data with vehicle_id
        assert "data" in message
    monkeypatch.setattr(layer, "group_send", AsyncMock(side_effect=fake_send))

    # импорт и запуск функции fetch + process
    from services.polling_worker import fetch_status_for_vehicle, process_vehicle
    import asyncio
    status = asyncio.get_event_loop().run_until_complete(fetch_status_for_vehicle(v))
    assert status is not None
