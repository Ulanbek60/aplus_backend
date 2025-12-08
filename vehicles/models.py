from django.db import models
from users.models import CustomUser  # твоя модель пользователя (в users/models.py)


class Vehicle(models.Model):
    veh_id = models.IntegerField(unique=True)
    imei = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    type = models.CharField(max_length=64, null=True, blank=True)

    # Дизайн-поля
    plate_number = models.CharField(max_length=20, null=True, blank=True)
    vin = models.CharField(max_length=64, null=True, blank=True)
    mileage = models.IntegerField(default=0)
    to_remaining = models.IntegerField(default=0)
    location_name = models.CharField(max_length=255, null=True, blank=True)

    # Фото
    photo_front = models.CharField(max_length=255, null=True, blank=True)
    photo_back = models.CharField(max_length=255, null=True, blank=True)

    # Реальное время
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    fuel = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, default="active")

    updated_at = models.DateTimeField(auto_now=True)


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


class VehicleAssignment(models.Model):
    # vehicle - FK на Vehicle
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE)    # привязка к технике
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE)         # водитель (юзер)
    assigned_at = models.DateTimeField(auto_now_add=True)              # дата привязки
    unassigned_at = models.DateTimeField(null=True, blank=True)        # дата открепления (если есть)

    class Meta:
        # индекс на vehicle для быстрых запросов
        indexes = [models.Index(fields=["vehicle", "driver"])]


class Repair(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    date = models.DateField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parts = models.JSONField(blank=True, null=True)  # список запчастей
    cost_parts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_work = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, default="done")


