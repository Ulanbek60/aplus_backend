from django.db import models

class User(models.Model):
    ROLE_CHOICES = [
        ('driver', 'Driver'),
        ('mechanic', 'Mechanic'),
    ]

    STATUS_CHOICES = [
        ('registration', 'Registration'),
        ('pending_vehicle', 'Pending vehicle approval'),
        ('active', 'Active'),
    ]

    telegram_id = models.BigIntegerField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    surname = models.CharField(max_length=50, blank=True, null=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='driver')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='registration')
    language = models.CharField(max_length=5, default='ru')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} {self.surname} ({self.telegram_id})"


class VehicleRequest(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_id = models.CharField(max_length=50)   # ID из Инкомтека
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
