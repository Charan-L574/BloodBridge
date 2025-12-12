from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
import json

from database import create_db_and_tables, get_session
from routes import auth_routes, location_routes, blood_request_routes, hospital_routes, notification_routes
from websocket_manager import (
    manager, get_websocket_user,
    handle_location_update, handle_stop_live_tracking,
    handle_watch_request
)

app = FastAPI(
    title="BloodBridge",
    description="Real-time Blood Donation Platform API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(location_routes.router)
app.include_router(blood_request_routes.router)
app.include_router(hospital_routes.router)
app.include_router(notification_routes.router)


@app.on_event("startup")
async def on_startup():
    """Initialize database and ML models on startup"""
    create_db_and_tables()
    
    # Initialize ML models with real data
    print("\n🤖 Starting ML model initialization...")
    try:
        from ml_training import initialize_ml_models
        from database import engine
        with Session(engine) as session:
            initialize_ml_models(session)
    except Exception as e:
        print(f"⚠️ ML model initialization warning: {e}")
        print("💡 Models will use synthetic data for now. Train with real data via /blood-requests/ml/retrain/all")
    
    # Start background training scheduler
    print("\n🔄 Starting adaptive training scheduler...")
    try:
        from training_scheduler import start_background_training
        await start_background_training()
        print("✅ Adaptive training scheduler started (checks every hour)")
    except Exception as e:
        print(f"⚠️ Background scheduler warning: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on shutdown"""
    print("\n🛑 Shutting down...")
    try:
        from training_scheduler import stop_background_training
        await stop_background_training()
    except Exception as e:
        print(f"⚠️ Shutdown warning: {e}")


@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "message": "BloodBridge API",
        "version": "1.0.0",
        "status": "running"
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time features
    
    Message types:
    - location_update: Live location from donor
    - watch_request: Start watching a blood request
    - stop_tracking: Stop live tracking
    """
    # Authenticate
    user_data = await get_websocket_user(websocket, token)
    if not user_data:
        return
    
    # Get user_id from email in token
    email = user_data.get("sub")
    if not email:
        print("❌ No email in token, closing connection")
        await websocket.close(code=1008)
        return
    
    # Look up user by email to get user_id
    from sqlmodel import select
    from models import User
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if not user:
            print(f"❌ User not found for email {email}, closing connection")
            await websocket.close(code=1008)
            return
        user_id = user.id
    
    print(f"✅ WebSocket authenticated: user_id={user_id}, email={email}")
    
    # Connect
    await manager.connect(websocket, user_id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established"
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            message_data = message.get("data", {})
            
            # Get database session for this operation
            with Session(engine) as session:
                if message_type == "location_update":
                    await handle_location_update(message_data, session)
                elif message_type == "stop_tracking":
                    await handle_stop_live_tracking(message_data, session)
                elif message_type == "watch_request":
                    await handle_watch_request(message_data, websocket)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# Import engine for WebSocket session
from database import engine


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
