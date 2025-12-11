from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vehicle, VehicleStatusHistory, FuelLevelHistory, TrackPoint, Event, Repair, Vehicle
from .serializers import (
    VehicleStatusHistorySerializer,
    FuelLevelHistorySerializer,
    TrackPointSerializer,
    EventSerializer,
    VehicleDetailSerializer,
    RepairSerializer,
    VEHICLE_FUEL_CAPACITY_DEFAULT,
    FrontendVehicleSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from services.pilot_client import pilot_request_sync
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly



class VehicleViewSet(viewsets.ViewSet):

    # GET /api/vehicles/
    def list(self, request):
        data = pilot_request_sync("list", 14)
        result = []

        for v in data.get("list", []):
            fuel = None
            for s in v.get("sensors_status", []):
                if s.get("name") == "топливо":
                    try:
                        fuel = float(s.get("dig_value"))
                    except:
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

    # GET /api/vehicles/<id>/status/
    @action(detail=True, methods=["get"])
    @swagger_auto_schema(
        operation_summary="Telemetry: status history",
        tags=["Telemetry"]
    )
    def status(self, request, pk=None):
        q = VehicleStatusHistory.objects.filter(vehicle__veh_id=pk).order_by("-ts")[:500]
        return Response(VehicleStatusHistorySerializer(q, many=True).data)

    # GET /api/vehicles/<id>/fuel/
    @action(detail=True, methods=["get"])
    def fuel(self, request, pk=None):
        q = FuelLevelHistory.objects.filter(vehicle__veh_id=pk).order_by("-ts")[:500]
        return Response(FuelLevelHistorySerializer(q, many=True).data)

    # GET /api/vehicles/<id>/events/
    @action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        q = Event.objects.filter(vehicle__veh_id=pk).order_by("-ts")[:200]
        return Response(EventSerializer(q, many=True).data)

    # GET /api/vehicles/<id>/track/
    @action(detail=True, methods=["get"])
    def track(self, request, pk=None):
        q = TrackPoint.objects.filter(vehicle__veh_id=pk).order_by("ts")
        return Response(TrackPointSerializer(q, many=True).data)


# from .serializers import , VEHICLE_FUEL_CAPACITY_DEFAULT

def make_vehicle_entry(v: Vehicle):
    return FrontendVehicleSerializer.from_vehicle_obj(
        v,
        capacity=VEHICLE_FUEL_CAPACITY_DEFAULT
    )


class DashboardStatsView(APIView):

    @swagger_auto_schema(
        operation_summary="Dashboard statistics",
        tags=["Dashboard"]
    )
    def get(self, request):

        vehicles = Vehicle.objects.all()

        # 1. Низкий уровень топлива (<20)
        low_fuel_qs = vehicles.filter(fuel__lt=20)
        low_fuel = [make_vehicle_entry(v) for v in low_fuel_qs]

        # 2. ACTIVE — машины с заведённым двигателем
        active_qs = vehicles.filter(ignition=True)
        active = [make_vehicle_entry(v) for v in active_qs]

        # 3. IDLE — машины с выключенным двигателем
        idle_qs = vehicles.filter(ignition=False)
        idle = [make_vehicle_entry(v) for v in idle_qs]

        # 4. ремонт / аренда (позже)
        rented = []
        repair = []

        return Response({
            "stats": {
                "count_rented": len(rented),
                "count_repair": len(repair),
                "count_active": len(active),
                "count_idle": len(idle),
                "count_low_fuel": len(low_fuel),
            },

            "rented": rented,
            "repair": repair,
            "active": active,
            "idle": idle,
            "low_fuel": low_fuel,
        })

    # GET /api/vehicles/<pk>/
    def retrieve(self, request, pk=None):
        # pk в твоём code — это veh_id (не id). Найдём по veh_id
        vehicle = get_object_or_404(Vehicle, veh_id=pk)
        serializer = VehicleDetailSerializer(vehicle)
        return Response(serializer.data)



class VehicleDetailView(APIView):

    @swagger_auto_schema(
        operation_summary="Detailed vehicle info",
        operation_description="""
Возвращает полную информацию о технике:
- название
- геопозиция
- топливо
- привязанный водитель
- фотографии
- пробег
- статус
        """,
        tags=["Vehicles"]
    )
    def get(self, request, vehicle_id):
        try:
            v = Vehicle.objects.get(veh_id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({"error": "vehicle_not_found"}, 404)

        ser = VehicleDetailSerializer(v)
        return Response(ser.data)



class VehicleRepairsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, vehicle_id):
        try:
            v = Vehicle.objects.get(veh_id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({"error": "vehicle_not_found"}, 404)
        q = Repair.objects.filter(vehicle=v).order_by("-date")
        return Response(RepairSerializer(q, many=True).data)

    def post(self, request, vehicle_id):
        try:
            v = Vehicle.objects.get(veh_id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({"error": "vehicle_not_found"}, 404)

        data = request.data.copy()
        data["vehicle"] = v.id
        ser = RepairSerializer(data=data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)
