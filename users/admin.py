from django.contrib import admin
from .models import CustomUser, VehicleRequest
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(VehicleRequest)