from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime
from typing import Optional, List, Dict, Any
from services.event_bus import subscribe_to_event

class NotificationService:
    def __init__(self):
        self.setup_event_listeners()
    
    def setup_event_listeners(self):
        # Subscribe to events that should trigger notifications
        subscribe_to_event("pathway:initialized", self.handle_pathway_initialized)
        subscribe_to_event("pathway:step:completed", self.handle_pathway_step_completed)
        subscribe_to_event("pathway:completed", self.handle_pathway_completed)
        subscribe_to_event("step:assigned", self.handle_step_assigned)
    
    def handle_pathway_initialized(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Handling pathway:initialized event: {event.id}")
    
    def handle_pathway_step_completed(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Handling pathway:step:completed event: {event.id}")
    
    def handle_pathway_completed(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Handling pathway:completed event: {event.id}")
    
    def handle_step_assigned(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"Handling step:assigned event: {event.id}")
    
    def create_notification(self, db: Session, data: schemas.NotificationCreate):
        notification = models.Notification(
            recipient_id=data.recipient_id,
            title=data.title,
            description=data.description,
            notification_type=data.notification_type,
            related_patient_id=data.related_patient_id,
            related_pathway_id=data.related_pathway_id,
            priority=data.priority,
            status="unread"
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    def mark_as_read(self, db: Session, notification_id: int):
        notification = db.query(models.Notification).filter(
            models.Notification.id == notification_id
        ).first()
        
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")
        
        notification.status = "read"
        notification.read_at = datetime.now()
        
        db.commit()
        db.refresh(notification)
        
        return notification
    
    def get_notifications_for_user(self, db: Session, user_id: int, limit: Optional[int] = None):
        query = db.query(models.Notification).filter(
            models.Notification.recipient_id == user_id
        ).order_by(models.Notification.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_unread_notifications_count(self, db: Session, user_id: int):
        return db.query(models.Notification).filter(
            models.Notification.recipient_id == user_id,
            models.Notification.status == "unread"
        ).count()

# Create a singleton instance
notification_service = NotificationService()

