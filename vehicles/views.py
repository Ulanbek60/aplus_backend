from rest_framework.views import APIView
from rest_framework.response import Response
from services.pilot_client import pilot_request_sync

class VehicleListView(APIView):
    def get(self, request):
        data = pilot_request_sync("list", 14)

        result = []

        for v in data.get("list", []):
            fuel = None
            for s in v.get("sensors_status", []):
                if s.get("name") == "топливо":
                    try:
                        fuel = float(s.get("dig_value"))
                    except Exception:
                        fuel = None

            result.append({
                "id": v["veh_id"],
                "name": v.get("vehiclenumber"),
                "type": v.get("type"),
                "lat": float(v.get("status", {}).get("lat", 0) or 0),
                "lon": float(v.get("status", {}).get("lon", 0) or 0),
                "fuel": fuel
            })

        return Response(result)
