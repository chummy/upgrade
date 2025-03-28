from sqlalchemy.orm import Session
import models
from typing import Dict, Any, Callable, List
import json

# Event handlers registry
event_handlers: Dict[str, List[Callable]] = {}

def publish_event(db: Session, event_data: Dict[str, Any]):
    """
    Publish an event to the event bus
    """
    # Store event in database
    event = models.Event(
        event_type=event_data["event_type"],
        aggregate_type=event_data["aggregate_type"],
        aggregate_id=event_data["aggregate_id"],
        data=event_data["data"],
        metadata=event_data.get("metadata", {})
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Execute handlers
    handlers = event_handlers.get(event_data["event_type"], [])
    for handler in handlers:
        try:
            handler(event)
        except Exception as e:
            print(f"Error in event handler for {event_data['event_type']}: {e}")
    
    return event

def subscribe_to_event(event_type: str, handler: Callable):
    """
    Subscribe to an event type
    """
    if event_type not in event_handlers:
        event_handlers[event_type] = []
    
    event_handlers[event_type].append(handler)
    
    # Return unsubscribe function
    def unsubscribe():
        event_handlers[event_type].remove(handler)
    
    return unsubscribe

def get_events_for_aggregate(db: Session, aggregate_type: str, aggregate_id: str):
    """
    Get all events for an aggregate
    """
    return db.query(models.Event).filter(
        models.Event.aggregate_type == aggregate_type,
        models.Event.aggregate_id == aggregate_id
    ).order_by(models.Event.created_at.asc()).all()
