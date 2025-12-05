from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle


class Command(BaseCommand):
    help = "Sync vehicles from Pilot API"

    def handle(self, *args, **kwargs):
        data = pilot_request_sync("list", 14)

        for obj in data.get("list", []):
            fuel = None
            for s in obj.get("sensors_status", []):
                if s.get("name") == "топливо":
                    try:
                        fuel = float(s.get("dig_value"))
                    except:
                        fuel = None

            Vehicle.objects.update_or_create(
                veh_id=obj["veh_id"],
                defaults={
                    "imei": obj["imei"],
                    "name": obj.get("vehiclenumber"),
                    "type": obj.get("type"),
                    "lat": float(obj.get("status", {}).get("lat") or 0),
                    "lon": float(obj.get("status", {}).get("lon") or 0),
                    "speed": float(obj.get("status", {}).get("speed") or 0),
                    "fuel": fuel,
                }
            )

        self.stdout.write("Vehicles synced OK")
