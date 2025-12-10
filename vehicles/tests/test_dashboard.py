from rest_framework.test import APITestCase
from vehicles.models import Vehicle, VehicleStatusHistory


class DashboardTest(APITestCase):

    def setUp(self):
        v1 = Vehicle.objects.create(veh_id=100, imei="111", lat=42.0, lon=74.0, fuel=10)
        v2 = Vehicle.objects.create(veh_id=200, imei="222", lat=41.0, lon=75.0, fuel=50)

        VehicleStatusHistory.objects.create(vehicle=v1, ts=1, lat=0, lon=0, ignition=False)
        VehicleStatusHistory.objects.create(vehicle=v2, ts=1, lat=0, lon=0, ignition=True)

    def test_dashboard(self):
        r = self.client.get("/api/vehicles/dashboard/")
        self.assertEqual(r.status_code, 200)
        data = r.data["stats"]

        self.assertEqual(data["count_low_fuel"], 1)
        self.assertEqual(data["count_active"], 1)
        self.assertEqual(data["count_idle"], 1)
