from rest_framework.test import APITestCase
from users.models import CustomUser


class ProfileTest(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(
            telegram_id=777,
            username="u777",
            email="u777@example.com",
            phone="+996500000000",
            role="driver",
            status="active",
            language="ru"
        )

    def test_profile(self):
        r = self.client.get("/api/users/profile/777/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["role"], "driver")
