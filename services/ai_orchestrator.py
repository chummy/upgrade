from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
import random
from services.event_bus import subscribe_to_event

class AIOrchestrator:
    def __init__(self):
        self.setup_event_listeners()
    
    def setup_event_listeners(self):
        # Subscribe to events that should trigger AI analysis
        subscribe_to_event("pathway:initialized", self.handle_pathway_initialized)
        subscribe_to_event("pathway:step:completed", self.handle_pathway_step_completed)
    
    def handle_pathway_initialized(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"AI handling pathway:initialized event: {event.id}")
    
    def handle_pathway_step_completed(self, event):
        # This would be implemented to handle the event
        # For now, we'll just print a message
        print(f"AI handling pathway:step:completed event: {event.id}")
    
    def generate_insight(self, db: Session, data: schemas.AIInsightCreate):
        # In a real implementation, we would use an AI model to generate insights
        # based on the context and patient data
        
        # For now, we'll simulate AI-generated insights
        title = ""
        description = ""
        confidence = Decimal("0.85")
        
        if data.insight_type == "care-gap":
            title = "Potential Care Gap Detected"
            description = "Patient may be missing recommended follow-up appointments based on their care history."
        elif data.insight_type == "recommendation":
            title = "Treatment Recommendation"
            description = "Consider adjusting medication schedule based on recent lab results and patient feedback."
        elif data.insight_type == "optimization":
            title = "Pathway Optimization Opportunity"
            description = "This step typically takes longer than estimated. Consider adjusting the timeline or providing additional resources."
        elif data.insight_type == "alert":
            title = "Clinical Alert"
            description = "Recent vital signs indicate potential concern. Recommend immediate clinical review."
            confidence = Decimal("0.92")
        
        # Create the insight in the database
        insight = models.AIInsight(
            title=title or data.title,
            description=description or data.description,
            insight_type=data.insight_type,
            related_patient_id=data.related_patient_id,
            related_pathway_id=data.related_pathway_id,
            confidence=confidence,
            status="pending"
        )
        
        db.add(insight)
        db.commit()
        db.refresh(insight)
        
        return insight
    
    def get_insights_for_patient(self, db: Session, patient_id: int, limit: Optional[int] = None):
        query = db.query(models.AIInsight).filter(
            models.AIInsight.related_patient_id == patient_id
        ).order_by(models.AIInsight.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_insights_for_pathway(self, db: Session, pathway_id: int, limit: Optional[int] = None):
        query = db.query(models.AIInsight).filter(
            models.AIInsight.related_pathway_id == pathway_id
        ).order_by(models.AIInsight.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update_insight_status(self, db: Session, insight_id: int, status: str, user_id: Optional[int] = None):
        insight = db.query(models.AIInsight).filter(
            models.AIInsight.id == insight_id
        ).first()
        
        if not insight:
            raise ValueError(f"Insight {insight_id} not found")
        
        insight.status = status
        insight.acted_on_at = datetime.now()
        insight.acted_on_by = user_id
        
        db.commit()
        db.refresh(insight)
        
        return insight

# Create a singleton instance
ai_orchestrator = AIOrchestrator()
