from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    # Telegram
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)

    # Basic personal info
    phone = models.CharField(max_length=20, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=5, default="ru")

    # Roles
    ROLE_CHOICES = [
        ("driver", "Driver"),
        ("mechanic", "Mechanic"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="driver")

    # Status
    STATUS_CHOICES = [
        ("registration", "Registration"),
        ("pending_vehicle", "Pending Vehicle Approval"),
        ("active", "Active")
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="registration")

    # Documents
    birthdate = models.DateField(null=True, blank=True)
    passport_id = models.CharField(max_length=20, null=True, blank=True)
    iin = models.CharField(max_length=14, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    passport_front = models.CharField(max_length=200, null=True, blank=True)
    passport_back = models.CharField(max_length=200, null=True, blank=True)
    driver_license = models.CharField(max_length=200, null=True, blank=True)
    selfie = models.CharField(max_length=200, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username} | {self.phone} | {self.telegram_id}"


class VehicleRequest(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} — {self.vehicle_id} ({self.status})"
