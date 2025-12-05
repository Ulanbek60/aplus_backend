from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle, VehicleStatusHistory


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        vehicles = Vehicle.objects.all()

        for v in vehicles:
            data = pilot_request_sync("status", 14, {"imei": v.imei})
            arr = data.get("data", [])

            if not arr:
                continue

            st = arr[0].get("status")
            sensors = arr[0].get("sensors_status", [])

            fuel = None
            for s in sensors:
                if s["name"] == "топливо":
                    fuel = float(s["dig_value"])
                    break

            VehicleStatusHistory.objects.create(
                vehicle=v,
                ts=int(st["unixtimestamp"]),
                lat=float(st["lat"]),
                lon=float(st["lon"]),
                speed=float(st.get("speed") or 0),
                ignition=(int(st.get("firing", 0)) == 1),
                fuel=fuel
            )

        self.stdout.write("Status synced")
