"""
NoxSuite FastAPI - WebSocket Manager
WebSocket connection management
"""

class WebSocketManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.connections = []
    
    async def connect(self, websocket):
        """Connect WebSocket"""
        pass