from rest_framework import serializers
from .models import VehicleStatusHistory, FuelLevelHistory, TrackPoint, Event


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
