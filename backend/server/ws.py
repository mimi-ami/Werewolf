class WebSocketManager:
    def __init__(self):
        self.clients = []

    async def broadcast(self, message: dict):
        for ws in self.clients:
            await ws.send_json(message)
