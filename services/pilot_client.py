import aiohttp
import json
from django.conf import settings
from asgiref.sync import async_to_sync

BASE_URL = settings.PILOT_API_URL
LOGIN = settings.PILOT_LOGIN
PASSWORD = settings.PILOT_PASSWORD


async def pilot_request(cmd: str, node: int = 14, params: dict | None = None) -> dict:
    params = params or {}
    query = {"cmd": cmd, "node": node, **params}
    timeout = aiohttp.ClientTimeout(total=10)

    auth = aiohttp.BasicAuth(LOGIN, PASSWORD)

    async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
        async with session.get(BASE_URL, params=query) as resp:
            text = await resp.text()

            # убираем BOM
            if text.startswith("\ufeff"):
                text = text.replace("\ufeff", "", 1)

            if resp.status != 200:
                raise RuntimeError(f"PILOT HTTP {resp.status}: {text}")

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON from PILOT: {text}")


def pilot_request_sync(cmd: str, node: int = 14, params: dict | None = None) -> dict:
    return async_to_sync(pilot_request)(cmd, node, params)
