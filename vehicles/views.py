from rest_framework.views import APIView
from rest_framework.response import Response
from services.pilot_client import pilot_request


class VehicleListView(APIView):
    async def get(self, request):
        # тянем данные с Инкомтека
        data = await pilot_request("list", 14)

        result = []

        for v in data.get("list", []):
            fuel = None
            for s in v.get("sensors_status", []):
                if s.get("name") == "топливо":
                    fuel = float(s.get("dig_value"))

            result.append({
                "id": v["veh_id"],
                "name": v["vehiclenumber"],
                "type": v["type"],
                "lat": float(v["status"]["lat"]),
                "lon": float(v["status"]["lon"]),
                "fuel": fuel
            })
        return Response(result)