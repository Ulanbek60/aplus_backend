from rest_framework import serializers
from .models import VehicleStatusHistory, FuelLevelHistory, TrackPoint, Event, Vehicle, VehicleAssignment, Repair


class VehicleStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleStatusHistory
        fields = "__all__"


class FuelLevelHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelLevelHistory
        fields = "__all__"


class TrackPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackPoint
        fields = "__all__"


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class SimpleVehicleSerializer(serializers.ModelSerializer):
    # простой сериализатор для списка
    class Meta:
        model = Vehicle
        fields = ["veh_id", "name", "type", "lat", "lon", "fuel"]

from rest_framework import serializers
from .models import Vehicle, VehicleAssignment, Repair


class VehicleDetailSerializer(serializers.ModelSerializer):
    driver = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    fuel_percent = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "name",
            "plate_number",
            "vin",
            "type",
            "fuel",
            "fuel_percent",
            "lat",
            "lon",
            "location",
            "driver",
            "mileage",
            "to_remaining",
            "photos",
            "status",
        ]

    def get_driver(self, obj):
        assign = (
            VehicleAssignment.objects
            .filter(vehicle=obj, unassigned_at__isnull=True)
            .select_related("driver")
            .first()
        )
        if not assign:
            return None

        user = assign.driver
        return {
            "id": user.id,
            "name": f"{user.first_name or user.username} {user.surname or ''}".strip(),
            "phone": user.phone
        }

    def get_location(self, obj):
        return {
            "lat": obj.lat,
            "lon": obj.lon,
            "address": obj.location_name,
        }

    def get_photos(self, obj):
        return {
            "front": obj.photo_front,
            "back": obj.photo_back
        }

    def get_fuel_percent(self, obj):
        if not obj.fuel:
            return None
        try:
            return f"{int(obj.fuel)}%"
        except:
            return None


class RepairSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repair
        fields = ["id", "vehicle", "date", "title", "description", "parts", "cost_parts", "cost_work", "status"]
        read_only_fields = ["id", "vehicle"]


