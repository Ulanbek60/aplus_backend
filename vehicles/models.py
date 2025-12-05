from django.db import models


class Vehicle(models.Model):
    veh_id = models.IntegerField(unique=True)
    imei = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=64, null=True, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    fuel = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or self.imei}"


class Track(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    track_id = models.BigIntegerField()
    start_ts = models.BigIntegerField()
    end_ts = models.BigIntegerField()
    raw_track = models.TextField()

    def __str__(self):
        return f"Track {self.track_id} for {self.vehicle}"



class FuelLevelHistory(models.Model):
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE)
    ts = models.BigIntegerField()
    fuel = models.FloatField()

    class Meta:
        ordering = ['-ts']
        indexes = [models.Index(fields=['vehicle', 'ts'])]



class TrackPoint(models.Model):
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE)
    ts = models.BigIntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    speed = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-ts']
        indexes = [models.Index(fields=['vehicle', 'ts'])]


class Event(models.Model):
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE)
    ts = models.BigIntegerField()
    event_type = models.CharField(max_length=64)
    value = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['-ts']
        indexes = [models.Index(fields=['vehicle', 'ts'])]


class Geozone(models.Model):
    zone_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    zonetype = models.IntegerField()  # 1 polygon, 2 circle
    color = models.CharField(max_length=16, null=True, blank=True)
    geometry = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.name

class VehicleStatusHistory(models.Model):
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE)
    ts = models.BigIntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    speed = models.FloatField(null=True, blank=True)
    ignition = models.BooleanField(default=False)
    fuel = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-ts"]
        indexes = [models.Index(fields=["vehicle", "ts"])]


