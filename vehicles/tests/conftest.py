import pytest
from users.models import CustomUser

@pytest.fixture
def user():
    return CustomUser.objects.create(
        telegram_id=777,
        username="testuser",
        phone="+996500000000",
        role="driver",
        status="active",
        language="ru",
    )
