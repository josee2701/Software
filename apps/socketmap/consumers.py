import asyncio
import json
import re
from datetime import datetime, timedelta, timezone

import aioredis
from channels.generic.websocket import AsyncWebsocketConsumer


class GPSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "gps_updates"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Crear la conexión a Redis
        self.redis = aioredis.from_url(
            "redis://redis-cip", encoding="utf-8", decode_responses=True
        )
        self.last_update_check = datetime.utcnow().replace(
            tzinfo=timezone.utc
        )  # Inicializar aquí
        # Realizar el cargue inicial de datos
        await self.initial_data_load()

        # Iniciar la escucha de eventos de Redis
        asyncio.create_task(self.send_updates())

    async def initial_data_load(self):
        keys = await self.redis.keys("*")
        keys_to_exclude = [
            "command_response",
            "commands",
            "fmbxxx",
            "asgi:group:gps_updates",
        ]
        numeric_key_pattern = re.compile(r"^\d+$")
        all_values = {}
        for key in keys:
            if key not in keys_to_exclude and numeric_key_pattern.match(key):
                # Usar el comando de ReJSON para obtener el objeto JSON almacenado en la clave
                value = await self.redis.execute_command("JSON.GET", key)
                if value:
                    # Convertir la cadena JSON a un objeto Python y agregar al diccionario
                    all_values[key] = json.loads(value)
        # Enviar todos los valores JSON recuperados a través de WebSocket
        await self.send(text_data=json.dumps(all_values))

    async def disconnect(self, close_code):
        # Asegúrate de cerrar la conexión de Redis adecuadamente
        await self.redis.close()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_updates(self):
        keys_to_exclude = [
            "command_response",
            "commands",
            "fmbxxx",
            "asgi:group:gps_updates",
        ]
        numeric_key_pattern = re.compile(r"^\d+$")
        while True:
            all_keys = await self.redis.keys("*")  # Considera usar SCAN en producción
            all_values = {}
            for key in all_keys:
                if key not in keys_to_exclude and numeric_key_pattern.match(key):
                    json_value = await self.redis.execute_command("JSON.GET", key)
                    if json_value:
                        all_values[key] = json.loads(json_value)
            if all_values:
                await self.send(text_data=json.dumps(all_values))
            await asyncio.sleep(
                0.5
            )  # Espera 1 segundo antes de enviar la siguiente actualización
