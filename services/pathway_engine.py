from sqlalchemy.orm import Session
import models
import schemas
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random
from services.event_bus import publish_event

class PathwayEngine:
    def initialize_pathway(self, db: Session, data: schemas.PatientPathwayCreate):
        # Get the template
        template = db.query(models.PathwayTemplate).filter(
            models.PathwayTemplate.id == data.template_id
        ).first()
        
        if not template:
            raise ValueError(f"Pathway template {data.template_id} not found")
        
        # Get the steps
        steps = db.query(models.PathwayStep).filter(
            models.PathwayStep.template_id == template.id
        ).order_by(models.PathwayStep.step_order).all()
        
        if not steps:
            raise ValueError(f"Pathway template {data.template_id} has no steps")
        
        # Calculate estimated end date
        total_duration = sum(step.estimated_duration or 0 for step in steps)
        estimated_end_date = datetime.now() + timedelta(days=total_duration)
        
        # Create the pathway
        pathway = models.PatientPathway(
            patient_id=data.patient_id,
            template_id=data.template_id,
            current_step_id=steps[0].id,
            status="active",
            start_date=datetime.now(),
            estimated_end_date=estimated_end_date,
            created_by=data.created_by_id
        )
        
        db.add(pathway)
        db.commit()
        db.refresh(pathway)
        
        # Publish event
        publish_event(db, {
            "event_type": "pathway:initialized",
            "aggregate_type": "pathway",
            "aggregate_id": str(pathway.id),
            "data": {
                "pathway_id": pathway.id,
                "patient_id": pathway.patient_id,
                "template_id": pathway.template_id,
                "current_step_id": pathway.current_step_id
            }
        })
        
        return pathway
    
    def complete_step(self, db: Session, pathway_id: int, data: schemas.CompleteStepRequest):
        # Get the pathway
        pathway = db.query(models.PatientPathway).filter(
            models.PatientPathway.id == pathway_id
        ).first()
        
        if not pathway:
            raise ValueError(f"Pathway {pathway_id} not found")
        
        if pathway.current_step_id != data.step_id:
            raise ValueError(f"Step {data.step_id} is not the current step for pathway {pathway_id}")
        
        # Start a transaction
        try:
            # Mark step as completed
            completed_step = models.CompletedStep(
                pathway_id=pathway_id,
                step_id=data.step_id,
                completed_by=data.completed_by_id,
                notes=data.notes
            )
            db.add(completed_step)
            
            # Get decision points for this step
            decision_point = db.query(models.DecisionPoint).filter(
                models.DecisionPoint.step_id == data.step_id
            ).first()
            
            next_step_id = None
            is_pathway_completed = False
            
            if decision_point:
                # In a real implementation, we would evaluate the condition
                # For now, we'll just randomly choose true or false
                condition_result = random.random() > 0.5
                next_step_id = decision_point.true_step_id if condition_result else decision_point.false_step_id
            else:
                # Find the next sequential step
                template = db.query(models.PathwayTemplate).join(
                    models.PatientPathway, models.PathwayTemplate.id == models.PatientPathway.template_id
                ).filter(models.PatientPathway.id == pathway_id).first()
                
                steps = db.query(models.PathwayStep).filter(
                    models.PathwayStep.template_id == template.id
                ).order_by(models.PathwayStep.step_order).all()
                
                current_step_index = next((i for i, step in enumerate(steps) if step.id == data.step_id), -1)
                
                if current_step_index < len(steps) - 1:
                    next_step_id = steps[current_step_index + 1].id
            
            # Update the pathway
            if next_step_id:
                pathway.current_step_id = next_step_id
                pathway.updated_at = datetime.now()
            else:
                # No next step, pathway is complete
                is_pathway_completed = True
                pathway.status = "completed"
                pathway.actual_end_date = datetime.now()
                pathway.current_step_id = None
                pathway.updated_at = datetime.now()
            
            db.commit()
            db.refresh(pathway)
            
            # Publish event
            publish_event(db, {
                "event_type": "pathway:step:completed",
                "aggregate_type": "pathway",
                "aggregate_id": str(pathway_id),
                "data": {
                    "pathway_id": pathway_id,
                    "step_id": data.step_id,
                    "completed_by_id": data.completed_by_id,
                    "next_step_id": next_step_id
                }
            })
            
            if is_pathway_completed:
                publish_event(db, {
                    "event_type": "pathway:completed",
                    "aggregate_type": "pathway",
                    "aggregate_id": str(pathway_id),
                    "data": {
                        "pathway_id": pathway_id,
                        "patient_id": pathway.patient_id
                    }
                })
            
            return pathway
            
        except Exception as e:
            db.rollback()
            raise e
    
    def get_patient_pathway(self, db: Session, pathway_id: int):
        return db.query(models.PatientPathway).filter(
            models.PatientPathway.id == pathway_id
        ).first()
    
    def get_patient_pathways(self, db: Session, patient_id: int):
        return db.query(models.PatientPathway).filter(
            models.PatientPathway.patient_id == patient_id
        ).order_by(models.PatientPathway.created_at.desc()).all()
    
    def get_active_pathways(self, db: Session, limit: Optional[int] = None):
        query = db.query(models.PatientPathway).filter(
            models.PatientPathway.status == "active"
        ).order_by(models.PatientPathway.updated_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

# Create a singleton instance
pathway_engine = PathwayEngine()
