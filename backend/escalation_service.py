"""
Escalation service for blood requests
Handles retry logic and radius expansion when no donors respond
"""
from datetime import datetime, timedelta
from sqlmodel import Session, select
from typing import List
import asyncio

from models import BloodRequest, DonorResponse, RequestStatus, DonorResponseStatus, User, UserRole
from utils import get_compatible_blood_groups
from websocket_manager import connection_manager


class EscalationService:
    """Service to handle blood request escalation"""
    
    def __init__(self):
        self.initial_radius_km = 5.0
        self.escalation_steps = [10.0, 20.0, 50.0]  # Expand radius in steps
        self.response_timeout_minutes = 15  # Wait 15 minutes before escalation
    
    async def check_and_escalate(self, session: Session):
        """Check pending requests and escalate if needed"""
        # Find pending requests older than timeout
        timeout_threshold = datetime.utcnow() - timedelta(minutes=self.response_timeout_minutes)
        
        statement = select(BloodRequest).where(
            BloodRequest.status == RequestStatus.PENDING,
            BloodRequest.created_at < timeout_threshold
        )
        pending_requests = session.exec(statement).all()
        
        for request in pending_requests:
            await self._escalate_request(request, session)
    
    async def _escalate_request(self, request: BloodRequest, session: Session):
        """Escalate a single request"""
        # Check if any donors have accepted
        statement = select(DonorResponse).where(
            DonorResponse.blood_request_id == request.id,
            DonorResponse.status == DonorResponseStatus.ACCEPTED,
            DonorResponse.is_eligible == True
        )
        accepted_responses = session.exec(statement).all()
        
        if accepted_responses:
            # Request has been accepted, no need to escalate
            return
        
        # Count total responses (including rejected)
        statement = select(DonorResponse).where(
            DonorResponse.blood_request_id == request.id
        )
        total_responses = len(session.exec(statement).all())
        
        # Determine escalation level based on response count
        escalation_level = min(total_responses // 3, len(self.escalation_steps) - 1)
        new_radius = self.escalation_steps[escalation_level]
        
        # Log escalation
        print(f"Escalating request {request.id} to radius {new_radius} km (level {escalation_level})")
        
        # Notify requester about escalation
        await connection_manager.send_notification(
            request.requester_id,
            "request_escalated",
            {
                "request_id": request.id,
                "message": f"Expanding search radius to {new_radius} km to find more donors",
                "new_radius_km": new_radius
            }
        )
        
        # Find and notify additional donors in expanded radius
        compatible_groups = get_compatible_blood_groups(request.blood_group)
        
        statement = select(User).where(
            User.role == UserRole.DONOR,
            User.blood_group.in_(compatible_groups),
            User.is_available == True
        )
        all_donors = session.exec(statement).all()
        
        # Filter donors who haven't been notified yet
        statement = select(DonorResponse.donor_id).where(
            DonorResponse.blood_request_id == request.id
        )
        notified_donor_ids = [d for d in session.exec(statement).all()]
        
        new_donors = [d for d in all_donors if d.id not in notified_donor_ids]
        
        # Notify new donors
        for donor in new_donors[:10]:  # Notify up to 10 new donors per escalation
            await connection_manager.send_notification(
                donor.id,
                "blood_request_urgent",
                {
                    "request_id": request.id,
                    "blood_group": request.blood_group.value,
                    "urgency_level": request.urgency_level,
                    "message": f"Urgent: No donors have responded yet. Your help is needed!",
                    "escalation_level": escalation_level + 1
                }
            )


# Global escalation service instance
escalation_service = EscalationService()


async def start_escalation_monitor(session: Session):
    """Background task to monitor and escalate requests"""
    while True:
        try:
            await escalation_service.check_and_escalate(session)
        except Exception as e:
            print(f"Escalation monitor error: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)
