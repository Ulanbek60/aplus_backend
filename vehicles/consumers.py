# vehicles/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model

class VehicleStatusConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # проверяем query string token ?token=xxx&vehicle=123
        qs = parse_qs(self.scope.get("query_string").decode() or "")
        token = qs.get("token", [None])[0]
        vehicle = qs.get("vehicle", [None])[0]

        # TODO: валидировать token — если у тебя JWT/сессии, провалидировать его
        # временно: разрешаем подключение (но лучше валидировать)
        if not token:
            await self.close(code=4001)
            return

        self.user_token = token
        self.sub_vehicle = vehicle

        # Глобальная группа (дешборд)
        await self.channel_layer.group_add("vehicles:global", self.channel_name)

        # Если подписка на конкретную машину — добавляем группу
        if vehicle:
            await self.channel_layer.group_add(f"vehicle:{vehicle}", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("vehicles:global", self.channel_name)
        if getattr(self, "sub_vehicle", None):
            await self.channel_layer.group_discard(f"vehicle:{self.sub_vehicle}", self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # клиент ничего не посылает в нашем сценарии, но можно поддержать heartbeat
        pass

    async def send_update(self, event):
        # event["data"] — готовая структура
        await self.send(text_data=json.dumps(event["data"]))
