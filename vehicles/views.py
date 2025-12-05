from rest_framework.views import APIView
from rest_framework.response import Response
from services.pilot_client import pilot_request_sync
from .models import VehicleStatusHistory, FuelLevelHistory, TrackPoint, Event
from .serializers import VehicleStatusHistorySerializer, FuelLevelHistorySerializer, TrackPointSerializer, EventSerializer


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


class VehicleStatusHistoryView(APIView):
    def get(self, request, veh_id):
        q = VehicleStatusHistory.objects.filter(vehicle__veh_id=veh_id).order_by("-ts")[:500]
        return Response(VehicleStatusHistorySerializer(q, many=True).data)


class FuelHistoryView(APIView):
    def get(self, request, veh_id):
        q = FuelLevelHistory.objects.filter(vehicle__veh_id=veh_id).order_by("-ts")[:500]
        return Response(FuelLevelHistorySerializer(q, many=True).data)


class TrackView(APIView):
    def get(self, request, veh_id):
        q = TrackPoint.objects.filter(vehicle__veh_id=veh_id).order_by("ts")
        return Response(TrackPointSerializer(q, many=True).data)


class EventView(APIView):
    def get(self, request, veh_id):
        q = Event.objects.filter(vehicle__veh_id=veh_id).order_by("-ts")[:300]
        return Response(EventSerializer(q, many=True).data)
