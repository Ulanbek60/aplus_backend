from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle, FuelLevelHistory


class Command(BaseCommand):
    help = "Sync fuel history"

    def handle(self, *args, **kwargs):
        for v in Vehicle.objects.all():
            data = pilot_request_sync("list", 14)
            sensors = None

            for obj in data.get("list", []):
                if obj["imei"] == v.imei:
                    sensors = obj.get("sensors_status", [])
                    break

            if not sensors:
                continue

            fuel_sensor = next((s for s in sensors if s["name"] == "топливо"), None)
            if not fuel_sensor:
                continue

            sensor_id = fuel_sensor["id"]

            history = pilot_request_sync("sensorhistory", 14, {
                "id": sensor_id,
                "from": 1700000000,  # TODO — параметризовать
                "to": 1799999999
            })

            for item in history.get("data", []):
                FuelLevelHistory.objects.update_or_create(
                    vehicle=v,
                    ts=item["ts"],
                    defaults={"fuel": float(item["value"])}
                )

        self.stdout.write("Fuel history synced")
