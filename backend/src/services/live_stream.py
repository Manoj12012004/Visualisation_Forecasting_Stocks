
from fastapi import WebSocket
from typing import List

# Global WebSocket connection list
active_connections: List[WebSocket] = []


