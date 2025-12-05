from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle, VehicleStatusHistory
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class Command(BaseCommand):
    help = "Sync status history"

    def handle(self, *args, **kwargs):

        channel_layer = get_channel_layer()  # у тебя ЭТОГО НЕ БЫЛО

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

            obj = VehicleStatusHistory.objects.create(
                vehicle=v,
                ts=int(status["unixtimestamp"]),
                lat=float(status["lat"]),
                lon=float(status["lon"]),
                speed=float(status.get("speed", 0)),
                ignition=(int(status.get("firing", 0)) == 1),
                fuel=fuel
            )

            # -----------------------------------
            # REAL-TIME PUSH
            # -----------------------------------
            async_to_sync(channel_layer.group_send)(
                "vehicles",
                {
                    "type": "send_update",
                    "data": {
                        "vehicle_id": v.veh_id,
                        "lat": obj.lat,
                        "lon": obj.lon,
                        "speed": obj.speed,
                        "ignition": obj.ignition,
                        "fuel": obj.fuel,
                        "ts": obj.ts,
                    }
                }
            )

        self.stdout.write("Status history synced + WebSocket pushed")
