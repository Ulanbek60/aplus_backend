from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle, VehicleStatusHistory


class Command(BaseCommand):
    help = "Sync status history"

    def handle(self, *args, **kwargs):
        for v in Vehicle.objects.all():
            data = pilot_request_sync("status", 14, {"imei": v.imei})
            arr = data.get("data", [])

            if not arr:
                continue

            status = arr[0].get("status")
            sensors = arr[0].get("sensors_status", [])

            fuel = None
            for s in sensors:
                if s["name"] == "топливо":
                    fuel = float(s["dig_value"])
                    break

            VehicleStatusHistory.objects.create(
                vehicle=v,
                ts=int(status["unixtimestamp"]),
                lat=float(status["lat"]),
                lon=float(status["lon"]),
                speed=float(status.get("speed", 0)),
                ignition=(int(status.get("firing", 0)) == 1),
                fuel=fuel
            )

        self.stdout.write("Status history synced")
