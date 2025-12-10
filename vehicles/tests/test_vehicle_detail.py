from rest_framework.test import APITestCase
from vehicles.models import Vehicle


class VehicleDetailTest(APITestCase):

    def setUp(self):
        Vehicle.objects.create(
            veh_id=999,
            imei="333",
            name="Test Truck",
            type="Lorry",
            fuel=73,
            lat=42.88,
            lon=74.59,
        )

    def test_detail(self):
        r = self.client.get("/api/vehicles/999/detail/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["name"], "Test Truck")
