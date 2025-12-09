# services/polling_worker.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aplus_backend.settings")
django.setup()

# async polling worker that queries PILOT API and pushes updates to channels
import asyncio                                              # для event loop и sleep
from asgiref.sync import sync_to_async                       # чтобы вызывать ORM синхронно
from channels.layers import get_channel_layer                # для получения layer
from vehicles.models import Vehicle, VehicleStatusHistory    # модели
from services.pilot_client import pilot_request              # асинхронный клиент pilot

# в этом примере используем период опроса 2 секунды
POLL_INTERVAL = 2.0                                        # интервал опроса в секундах

async def fetch_status_for_vehicle(v: Vehicle):
    # Здесь вызываем pilot_request асинхронно и возвращаем результат
    # pilot_request — асинхронная функция, поэтому await
    data = await pilot_request("status", 14, {"imei": v.imei})  # опрашиваем инкомтек
    arr = data.get("data", []) if isinstance(data, dict) else []
    if not arr:
        return None
    status = arr[0].get("status", {})
    sensors = arr[0].get("sensors_status", [])
    fuel = None
    # попробуем достать топливо
    for s in sensors:
        if s.get("name") == "топливо":
            try:
                fuel = float(s.get("dig_value"))
            except Exception:
                fuel = None
            break
    return {
        "ts": int(status.get("unixtimestamp", 0)),
        "lat": float(status.get("lat", 0) or 0),
        "lon": float(status.get("lon", 0) or 0),
        "speed": float(status.get("speed", 0) or 0),
        "ignition": (int(status.get("firing", 0)) == 1),
        "fuel": fuel
    }

@sync_to_async
def get_all_vehicles_sync():
    # sync ORM call to get vehicles — вызывается в threadpool
    return list(Vehicle.objects.all())

@sync_to_async
def save_status_history_sync(vehicle_obj, item):
    # сохраняем точку статуса в БД синхронно (в threadpool)
    return VehicleStatusHistory.objects.create(
        vehicle=vehicle_obj,
        ts=item["ts"],
        lat=item["lat"],
        lon=item["lon"],
        speed=item["speed"],
        ignition=item["ignition"],
        fuel=item["fuel"]
    )

async def process_vehicle(channel_layer, v):
    # для каждой машины делаем запрос
    status = await fetch_status_for_vehicle(v)                # получаем статус от Pilot
    if not status:
        return
    # сохраняем историю (DB sync через sync_to_async)
    obj = await save_status_history_sync(v, status)          # записываем в VehicleStatusHistory
    # формируем payload для фронта
    payload = {
        "vehicle_id": v.veh_id,
        "lat": obj.lat,
        "lon": obj.lon,
        "speed": obj.speed,
        "ignition": obj.ignition,
        "fuel": obj.fuel,
        "ts": obj.ts,
    }
    # отправляем в глобальную группу
    await channel_layer.group_send("vehicles", {"type": "send_update", "data": payload})
    # отправляем в конкретную per-vehicle группу
    await channel_layer.group_send(f"vehicle_{v.veh_id}", {"type": "send_update", "data": payload})

async def polling_loop():
    # основной цикл
    print("🚀 Starting ASYNC-SAFE Polling Worker...")         # лог
    channel_layer = get_channel_layer()                       # получаем layer (async)
    while True:
        vehicles = await get_all_vehicles_sync()              # получаем список машин
        print(f"[INFO] Polling {len(vehicles)} vehicles...")  # лог
        tasks = [process_vehicle(channel_layer, v) for v in vehicles]  # создаём таски
        # выполняем параллельно с ожиданием завершения всех задач
        if tasks:
            await asyncio.gather(*tasks)
        await asyncio.sleep(POLL_INTERVAL)                    # ждём следующий раунд

if __name__ == "__main__":
    # запускаем цикл
    asyncio.run(polling_loop())
