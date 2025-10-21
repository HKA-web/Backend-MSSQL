from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MssqlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({"message": f"Hello {self.user_id}", "data": data}))
