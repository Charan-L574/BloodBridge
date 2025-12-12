from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from database import get_session
from models import Notification, User
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get user notifications"""
    statement = select(Notification).where(Notification.user_id == current_user.id)
    
    if unread_only:
        statement = statement.where(Notification.is_read == False)
    
    statement = statement.order_by(Notification.created_at.desc()).limit(limit)
    notifications = session.exec(statement).all()
    
    return notifications


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get count of unread notifications"""
    statement = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    count = len(session.exec(statement).all())
    
    return {"unread_count": count}


@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mark notification as read"""
    notification = session.get(Notification, notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    notification.is_read = True
    session.add(notification)
    session.commit()
    
    return {"message": "Notification marked as read"}


@router.put("/mark-all-read")
def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Mark all notifications as read"""
    statement = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    notifications = session.exec(statement).all()
    
    for notification in notifications:
        notification.is_read = True
        session.add(notification)
    
    session.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a notification"""
    notification = session.get(Notification, notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    session.delete(notification)
    session.commit()
    
    return {"message": "Notification deleted"}
