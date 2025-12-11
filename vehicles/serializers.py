from rest_framework import serializers
from .models import VehicleStatusHistory, FuelLevelHistory, TrackPoint, Event, Vehicle, VehicleAssignment, Repair
import re
from collections import Counter


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



VEHICLE_FUEL_CAPACITY_DEFAULT = 800.0  # литров

RUS_TO_LAT = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "У": "Y", "Х": "X"
})

class FrontendVehicleSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(allow_null=True)
    number = serializers.CharField(allow_null=True)
    driver = serializers.CharField(allow_null=True)
    fuel = serializers.FloatField(allow_null=True)
    fuel_percent = serializers.IntegerField(allow_null=True)


    @staticmethod
    def _find_plate(text: str):
        if not text:
            return None

        # Нормализация
        t = text.upper()
        t = t.translate(RUS_TO_LAT)
        t = re.sub(r'[_()\-]', ' ', t)
        t = re.sub(r'\s+', ' ', t)

        # Ищем нормальный номер
        m = re.search(r'\b\d{2}KG[0-9A-Z]{3,6}\b', t)
        if m:
            return m.group(0)

        return None

    @staticmethod
    def _clean_name(original: str, plate: str | None):
        if not original:
            return None

        s = original
        s = s.translate(RUS_TO_LAT)
        s = re.sub(r'[_()\-]', ' ', s)

        if plate:
            s = re.sub(re.escape(plate), ' ', s, flags=re.IGNORECASE)

        s = re.sub(r'\s+', ' ', s).strip()

        # Убираем одиночную мусорную букву "О" в начале ("О Субару" → "Субару")
        s = re.sub(r'^[ОO]\s+', '', s)

        # Финальный вид
        return s.strip() or None

    @staticmethod
    def from_vehicle_obj(v: 'Vehicle', capacity: float = VEHICLE_FUEL_CAPACITY_DEFAULT):
        # raw name from Pilot/DB
        raw_name = v.name or ""

        # try get plate from explicit plate_number field first
        plate = None
        if getattr(v, "plate_number", None):
            plate_candidate = str(v.plate_number).strip()
            plate_found = FrontendVehicleSerializer._find_plate(plate_candidate)
            if plate_found:
                plate = plate_found

        # if not from plate_number, try extract from raw_name
        if not plate:
            plate = FrontendVehicleSerializer._find_plate(raw_name)

        # clean name
        clean_name = FrontendVehicleSerializer._clean_name(raw_name, plate)

        # driver extraction (active assignment)
        driver = None
        try:
            from vehicles.models import VehicleAssignment  # avoid circular
            assign = VehicleAssignment.objects.filter(vehicle=v, unassigned_at__isnull=True).select_related("driver").first()
            if assign and assign.driver:
                user = assign.driver
                driver = f"{(user.first_name or user.username).strip()} {user.surname or ''}".strip() or None
        except Exception:
            driver = None

        # fuel and percent
        fuel = v.fuel if v.fuel is not None else None
        fuel_percent = None
        if fuel is not None:
            try:
                pct = int(round((float(fuel) / float(capacity)) * 100))
                pct = max(0, min(100, pct))
                fuel_percent = pct
            except Exception:
                fuel_percent = None

        return {
            "id": v.veh_id,
            "name": clean_name or None,
            "number": plate,
            "driver": driver,
            "fuel": fuel,
            "fuel_percent": fuel_percent
        }
