from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings



class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        extra_fields.setdefault("username", email.split("@")[0])

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("username", email.split("@")[0])
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)



class CustomUser(AbstractUser):
    # Telegram
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)

    # Personal info
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

    # AUTH
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} | {self.role}"


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
