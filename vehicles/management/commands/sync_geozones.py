from django.core.management.base import BaseCommand
from services.pilot_client import pilot_request_sync
from vehicles.models import Geozone


class Command(BaseCommand):
    help = "Sync geozones from Pilot"

    def handle(self, *args, **kwargs):
        data = pilot_request_sync("geofencelist", 14)

        zones = data.get("data", [])
        count = 0

        for z in zones:
            Geozone.objects.update_or_create(
                zone_id=z["id"],
                defaults={
                    "name": z["zonename"],
                    "zonetype": z["zonetype"],
                    "color": z.get("color"),
                    "geometry": z.get("geometry"),
                }
            )
            count += 1

        self.stdout.write(f"Imported geozones: {count}")
