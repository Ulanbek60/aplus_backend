from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import CustomUser, VehicleRequest


class FullRegisterTest(APITestCase):

    def test_full_register(self):
        url = "/api/users/full_register/"

        payload = {
            "telegram_id": 12345,
            "name": "John",
            "surname": "Doe",
            "birthdate": "1990-05-15",
            "phone": "+996500000000",
            "passport_id": "ID1234567",
            "iin": "12345678901234",
            "address": "Somewhere",
            "passport_front": "file1",
            "passport_back": "file2",
            "driver_license": "file3",
            "selfie": "file4",
            "language": "ru",
            "vehicle_id": "3881"
        }

        r = self.client.post(url, payload, format="json")
        self.assertEqual(r.status_code, 200)

        # user created
        user = CustomUser.objects.get(telegram_id=12345)
        self.assertEqual(user.status, "pending_vehicle")

        # vehicle request created
        req = VehicleRequest.objects.get(user=user)
        self.assertEqual(req.vehicle_id, "3881")
