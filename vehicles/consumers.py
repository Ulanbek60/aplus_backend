# vehicles/consumers.py
import json                                      # для сериализации/десериализации JSON
import jwt                                       # для декодирования JWT токена
from django.conf import settings                 # чтобы взять SECRET_KEY
from channels.generic.websocket import AsyncWebsocketConsumer  # базовый consumer
from channels.db import database_sync_to_async    # если нужно дернуть синхронную модель из async
from django.contrib.auth import get_user_model    # если захочешь вытаскивать пользователя
User = get_user_model()                           # ссылка на модель User

class VehicleStatusConsumer(AsyncWebsocketConsumer):
    # Consumer, который поддерживает: глобальную группу "vehicles" и per-vehicle "vehicle:<id>"
    async def connect(self):
        # При подключении: прочитаем token из querystring
        # self.scope["query_string"] — байты вида b'token=...'
        query = self.scope.get("query_string", b"").decode()  # читаем строку параметров
        token = None                                         # дефолт для токена
        # parse token=... простым способом
        for part in query.split("&"):                        # разбиваем параметры
            if part.startswith("token="):                    # если нашли token
                token = part.split("=", 1)[1]                # получаем его значение
                break                                        # выходим из цикла

        # без токена можно не пускать — или пустой доступ (решай)
        if not token:
            # отклоняем подключение если токена нет
            await self.close(code=4001)
            return

        # проверяем токен — если невалидный → close
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except Exception:
            # неверный токен — закрываем соединение
            await self.close(code=4002)
            return

        # В payload может быть поле user_id (или user_id string)
        user_id = payload.get("user_id")

        # Сохраняем user info в scope для дальнейшего использования (при необходимости)
        self.scope["user_id_from_token"] = user_id

        # Подключаем к глобальной группе "vehicles" — все клиенты её слушают
        await self.channel_layer.group_add("vehicles", self.channel_name)

        # Если клиент хочет подписаться на конкретную машину, он может подключиться к path /ws/vehicles/<id>/
        # Но если path содержит vehicle_id — добавим и в per-vehicle группу.
        vehicle_id = self.scope.get("url_route", {}).get("kwargs", {}).get("vehicle_id")
        if vehicle_id:
            await self.channel_layer.group_add(f"vehicle:{vehicle_id}", self.channel_name)

        # принимаем соединение
        await self.accept()

    async def disconnect(self, close_code):
        # при дисконнекте удаляем из групп
        try:
            await self.channel_layer.group_discard("vehicles", self.channel_name)
        except Exception:
            pass

        vehicle_id = self.scope.get("url_route", {}).get("kwargs", {}).get("vehicle_id")
        if vehicle_id:
            try:
                await self.channel_layer.group_discard(f"vehicle:{vehicle_id}", self.channel_name)
            except Exception:
                pass

    async def receive(self, text_data=None, bytes_data=None):
        # Клиент у нас ничего не шлёт, но если шлёт — можно обработать команды (ping/pong и т.п.)
        # Просто игнорируем
        return

    async def send_update(self, event):
        # Событие приходит из channel_layer.group_send с ключом "data"
        # Отправляем JSON клиенту
        await self.send(text_data=json.dumps(event["data"]))
