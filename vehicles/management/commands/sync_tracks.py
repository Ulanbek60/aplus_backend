from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Vehicle, TrackPoint


class Command(BaseCommand):
    help = "Sync track points"

    def handle(self, *args, **kwargs):
        for v in Vehicle.objects.all():
            data = pilot_request_sync("rungeo", 14, {
                "imei": v.imei,
                "start": 1700000000,
                "stop": 1799999999
            })

            for row in data.get("data", []):
                TrackPoint.objects.update_or_create(
                    vehicle=v,
                    ts=row["sec"],
                    defaults={
                        "lat": float(row["lat"]),
                        "lon": float(row["lon"]),
                        "speed": float(row["speed"])
                    }
                )

        self.stdout.write("Tracks synced")
