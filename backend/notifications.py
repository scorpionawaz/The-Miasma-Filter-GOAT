# notifications.py
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import WebSocket

class NotificationManager:
    def __init__(self):
        self.websocket: Optional[WebSocket] = None
    
    def set_websocket(self, websocket: WebSocket):
        self.websocket = websocket
    
    from datetime import datetime

    
    async def send(self, title: str, content: str, severity: str = "info", action: str = None):
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": "notification",
                    "title": title,
                    "content": content,
                    "severity": severity,
                    "action": action,
                    "timestamp": datetime.now().isoformat()  # ✅ fixed
                })
                print(f"✅ Sent: {title}")
            except Exception as e:
                print(f"❌ Failed to send: {e}")
    

# Global instance
notifier = NotificationManager()
