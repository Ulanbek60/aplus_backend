import aiohttp
import json
from django.conf import settings
from asgiref.sync import async_to_sync

async def pilot_request(cmd: str, node: int, params: dict | None = None) -> dict:
    if params is None:
        params = {}

    query = {"cmd": cmd, "node": node, **params}

    auth = aiohttp.BasicAuth(settings.PILOT_LOGIN, settings.PILOT_PASSWORD)
    url = settings.PILOT_API_URL

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
        async with session.get(url, params=query) as resp:
            text = await resp.text()

            # ### FIX: удаляем BOM ###
            if text.startswith("\ufeff"):
                text = text.replace("\ufeff", "", 1)

            if resp.status != 200:
                raise RuntimeError(f"PILOT HTTP {resp.status}: {text}")

            try:
                return json.loads(text)
            except Exception:
                raise RuntimeError(f"Invalid JSON from PILOT: {text}")

def pilot_request_sync(cmd: str, node: int, params: dict | None = None) -> dict:
    return async_to_sync(pilot_request)(cmd, node, params)
