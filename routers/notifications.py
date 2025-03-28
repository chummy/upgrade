from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from services.notification_service import notification_service

router = APIRouter()

@router.get("/", response_model=List[schemas.Notification])
def get_notifications(
    recipient_id: int,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1),
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.Notification).filter(
        models.Notification.recipient_id == recipient_id
    )
    
    # Apply status filter if provided
    if status:
        query = query.filter(models.Notification.status == status)
    
    # Get notifications
    notifications = query.order_by(models.Notification.created_at.desc()).limit(limit).all()
    
    return notifications

@router.post("/", response_model=schemas.Notification, status_code=201)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    try:
        return notification_service.create_notification(db, notification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")

@router.post("/{notification_id}/mark-as-read", response_model=schemas.Notification)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    try:
        return notification_service.mark_as_read(db, notification_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")
