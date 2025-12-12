from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
from datetime import datetime
import json
from sqlmodel import Session, select

from database import get_session
from models import DonorResponse, AuditLog
from auth import decode_access_token

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        # Map of user_id to WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of request_id to connected requesters
        self.request_watchers: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        print(f"🔗 WebSocket connected for user_id={user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            remaining = len(self.active_connections[user_id])
            print(f"🔌 WebSocket disconnected for user_id={user_id}. Remaining connections: {remaining}")
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                print(f"🗑️ Removed user_id={user_id} from active connections")
    
    async def watch_request(self, websocket: WebSocket, request_id: int):
        """Register a WebSocket to watch a specific blood request"""
        if request_id not in self.request_watchers:
            self.request_watchers[request_id] = set()
        self.request_watchers[request_id].add(websocket)
    
    def unwatch_request(self, websocket: WebSocket, request_id: int):
        """Unregister a WebSocket from watching a blood request"""
        if request_id in self.request_watchers:
            self.request_watchers[request_id].discard(websocket)
            if not self.request_watchers[request_id]:
                del self.request_watchers[request_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to a specific user (all their connections)"""
        print(f"📤 Attempting to send message to user_id={user_id}")
        print(f"   Active connections: {list(self.active_connections.keys())}")
        if user_id in self.active_connections:
            connection_count = len(self.active_connections[user_id])
            print(f"✅ Found {connection_count} connection(s) for user_id={user_id}")
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                    print(f"✅ Message sent successfully to user_id={user_id}")
                except Exception as e:
                    print(f"❌ Failed to send message: {e}")
        else:
            print(f"❌ No active connections for user_id={user_id}")
    
    async def broadcast_to_request_watchers(self, message: dict, request_id: int):
        """Broadcast message to all watchers of a blood request"""
        if request_id in self.request_watchers:
            disconnected = []
            for connection in self.request_watchers[request_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self.request_watchers[request_id].discard(connection)


manager = ConnectionManager()


async def get_websocket_user(websocket: WebSocket, token: str):
    """Authenticate WebSocket connection"""
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008)
        return None
    return payload


async def handle_location_update(data: dict, session: Session):
    """Handle live location update from donor"""
    donor_response_id = data.get("donor_response_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    
    if not all([donor_response_id, latitude, longitude]):
        return
    
    # Update donor response with current location
    statement = select(DonorResponse).where(DonorResponse.id == donor_response_id)
    donor_response = session.exec(statement).first()
    
    if donor_response:
        donor_response.current_latitude = latitude
        donor_response.current_longitude = longitude
        
        # Start tracking if not already started
        if not donor_response.live_tracking_started_at:
            donor_response.live_tracking_started_at = datetime.utcnow()
            
            # Log audit
            audit = AuditLog(
                user_id=donor_response.donor_id,
                action="live_tracking_started",
                entity_type="donor_response",
                entity_id=donor_response.id,
                details=json.dumps({"request_id": donor_response.blood_request_id})
            )
            session.add(audit)
        
        session.add(donor_response)
        session.commit()
        
        # Broadcast location update to request watchers
        await manager.broadcast_to_request_watchers(
            {
                "type": "location_update",
                "data": {
                    "donor_response_id": donor_response_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            donor_response.blood_request_id
        )


async def handle_stop_live_tracking(data: dict, session: Session):
    """Handle donor stopping live tracking"""
    donor_response_id = data.get("donor_response_id")
    
    if not donor_response_id:
        return
    
    statement = select(DonorResponse).where(DonorResponse.id == donor_response_id)
    donor_response = session.exec(statement).first()
    
    if donor_response:
        donor_response.live_tracking_stopped_at = datetime.utcnow()
        session.add(donor_response)
        
        # Log audit
        audit = AuditLog(
            user_id=donor_response.donor_id,
            action="live_tracking_stopped",
            entity_type="donor_response",
            entity_id=donor_response.id,
            details=json.dumps({"request_id": donor_response.blood_request_id})
        )
        session.add(audit)
        session.commit()
        
        # Notify request watchers
        await manager.broadcast_to_request_watchers(
            {
                "type": "tracking_stopped",
                "data": {
                    "donor_response_id": donor_response_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            donor_response.blood_request_id
        )


async def handle_watch_request(data: dict, websocket: WebSocket):
    """Handle request to watch a blood request"""
    request_id = data.get("request_id")
    if request_id:
        await manager.watch_request(websocket, request_id)


async def send_notification(user_id: int, notification_type: str, data: dict):
    """Send notification to a specific user"""
    await manager.send_personal_message(
        {
            "type": "notification",
            "notification_type": notification_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        },
        user_id
    )
