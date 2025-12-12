from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    DONOR = "donor"
    REQUESTER = "requester"
    HOSPITAL = "hospital"
    ADMIN = "admin"


class BloodGroup(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class VisibilityMode(str, Enum):
    SAVED_ONLY = "saved_only"
    LIVE_ONLY = "live_only"
    BOTH = "both"


class RequestStatus(str, Enum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class DonorResponseStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    DONATED = "donated"


# User Model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    phone: str
    role: UserRole
    blood_group: Optional[BloodGroup] = None
    age: Optional[int] = None
    weight: Optional[float] = None  # in kg
    
    # Donor-specific fields
    visibility_mode: Optional[VisibilityMode] = None
    last_donation_date: Optional[datetime] = None
    is_available: bool = True
    timezone: Optional[str] = None  # IANA timezone (e.g., "America/New_York", "Asia/Kolkata")
    
    # Hospital-specific fields
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    saved_locations: List["SavedLocation"] = Relationship(back_populates="user")
    blood_requests: List["BloodRequest"] = Relationship(back_populates="requester")
    donor_responses: List["DonorResponse"] = Relationship(back_populates="donor")
    hospital_inventory: List["HospitalInventory"] = Relationship(back_populates="hospital")


# Saved Location Model
class SavedLocation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    label: str  # e.g., "Home", "Office", "Gym"
    latitude: float
    longitude: float
    address: Optional[str] = None
    is_primary: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="saved_locations")


# Blood Request Model
class BloodRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    requester_id: int = Field(foreign_key="user.id")
    blood_group: BloodGroup
    units_needed: int = 1
    latitude: float
    longitude: float
    address: Optional[str] = None
    urgency_level: str = "normal"  # normal, urgent, critical
    description: Optional[str] = None
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    fulfilled_by_donor_id: Optional[int] = None  # ID of donor who provided blood
    fulfillment_source: Optional[str] = None  # "donor" or "other"
    
    # Relationships
    requester: Optional[User] = Relationship(back_populates="blood_requests")
    donor_responses: List["DonorResponse"] = Relationship(back_populates="blood_request")


# Donor Response Model
class DonorResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    blood_request_id: int = Field(foreign_key="bloodrequest.id")
    donor_id: int = Field(foreign_key="user.id")
    status: DonorResponseStatus = DonorResponseStatus.PENDING
    
    # Location tracking choices
    use_saved_location: bool = True
    saved_location_id: Optional[int] = Field(default=None, foreign_key="savedlocation.id")
    enable_live_tracking: bool = False
    
    # Current location (for live tracking)
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    
    # Eligibility check results
    is_eligible: bool = True
    eligibility_reasons: Optional[str] = None  # JSON string of reasons
    
    # ML ranking score
    ml_score: Optional[float] = None
    distance_km: Optional[float] = None
    
    responded_at: Optional[datetime] = None
    live_tracking_started_at: Optional[datetime] = None
    live_tracking_stopped_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    blood_request: Optional[BloodRequest] = Relationship(back_populates="donor_responses")
    donor: Optional[User] = Relationship(back_populates="donor_responses")


# Hospital Inventory Model
class HospitalInventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hospital_id: int = Field(foreign_key="user.id")
    blood_group: BloodGroup
    expiry_date: Optional[datetime] = None
    units_available: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    hospital: Optional[User] = Relationship(back_populates="hospital_inventory")


# Audit Log Model
class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = None
    action: str  # e.g., "donor_accepted", "live_tracking_started", "visibility_mode_changed"
    entity_type: str  # e.g., "blood_request", "donor_response", "user"
    entity_id: Optional[int] = None
    details: Optional[str] = None  # JSON string with additional info
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Notification Model
class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    notification_type: str  # e.g., "donor_accepted", "donation_confirmed", "request_fulfilled", "matching_request"
    title: str
    message: str
    data: Optional[str] = None  # JSON string with additional data
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Live Location Update (not stored in DB, for WebSocket)
class LiveLocationUpdate(SQLModel):
    donor_response_id: int
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
