# Import all route modules for easy access
from .auth_routes import router as auth_router
from .location_routes import router as location_router
from .blood_request_routes import router as blood_request_router
from .hospital_routes import router as hospital_router

__all__ = [
    "auth_router",
    "location_router",
    "blood_request_router",
    "hospital_router"
]
