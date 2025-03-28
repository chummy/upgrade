from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from services.notification_service import notification_service
from services.event_bus import publish_event
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[schemas.StepAssignment])
def get_assignments(
    pathway_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.StepAssignment)
    
    # Apply filters
    if pathway_id:
        query = query.filter(models.StepAssignment.pathway_id == pathway_id)
    
    if assigned_to_id:
        query = query.filter(models.StepAssignment.assigned_to_id == assigned_to_id)
    
    if status:
        query = query.filter(models.StepAssignment.status == status)
    
    # Get assignments
    assignments = query.order_by(models.StepAssignment.assigned_at.desc()).all()
    
    return assignments

@router.post("/", response_model=schemas.StepAssignment, status_code=201)
def create_assignment(assignment: schemas.StepAssignmentCreate, db: Session = Depends(get_db)):
    # Check if pathway exists
    pathway = db.query(models.PatientPathway).filter(
        models.PatientPathway.id == assignment.pathway_id
    ).first()
    
    if pathway is None:
        raise HTTPException(status_code=404, detail="Pathway not found")
    
    # Check if step exists
    step = db.query(models.PathwayStep).filter(
        models.PathwayStep.id == assignment.step_id
    ).first()
    
    if step is None:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Check if user exists
    user = db.query(models.User).filter(
        models.User.id == assignment.assigned_to_id
    ).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if assignment already exists
    existing_assignment = db.query(models.StepAssignment).filter(
        models.StepAssignment.pathway_id == assignment.pathway_id,
        models.StepAssignment.step_id == assignment.step_id
    ).first()
    
    if existing_assignment:
        raise HTTPException(status_code=400, detail="Assignment already exists for this step")
    
    # Create assignment
    db_assignment = models.StepAssignment(
        pathway_id=assignment.pathway_id,
        step_id=assignment.step_id,
        assigned_to_id=assignment.assigned_to_id,
        assigned_by_id=assignment.assigned_by_id,
        due_date=assignment.due_date,
        status=assignment.status,
        notes=assignment.notes
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    
    # Get patient details for notification
    patient = db.query(models.Patient).join(
        models.PatientPathway, models.Patient.id == models.PatientPathway.patient_id
    ).filter(
        models.PatientPathway.id == assignment.pathway_id
    ).first()
    
    # Send notification to assignee
    notification_service.create_notification(
        db,
        schemas.NotificationCreate(
            recipient_id=assignment.assigned_to_id,
            title="New Step Assignment",
            description=f"You have been assigned to step \"{step.name}\" for patient {patient.first_name} {patient.last_name}.",
            notification_type="assignment",
            related_patient_id=patient.id,
            related_pathway_id=assignment.pathway_id,
            priority="normal"
        )
    )
    
    # Publish event
    publish_event(
        db,
        {
            "event_type": "step:assigned",
            "aggregate_type": "assignment",
            "aggregate_id": str(db_assignment.id),
            "data": {
                "assignment_id": db_assignment.id,
                "pathway_id": assignment.pathway_id,
                "step_id": assignment.step_id,
                "assigned_to_id": assignment.assigned_to_id,
                "assigned_by_id": assignment.assigned_by_id
            }
        }
    )
    
    return db_assignment

@router.get("/{assignment_id}", response_model=schemas.StepAssignment)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(models.StepAssignment).filter(
        models.StepAssignment.id == assignment_id
    ).first()
    
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return assignment

@router.put("/{assignment_id}", response_model=schemas.StepAssignment)
def update_assignment(assignment_id: int, assignment: schemas.StepAssignmentUpdate, db: Session = Depends(get_db)):
    db_assignment = db.query(models.StepAssignment).filter(
        models.StepAssignment.id == assignment_id
    ).first()
    
    if db_assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Update assignment attributes
    if assignment.status is not None:
        db_assignment.status = assignment.status
    
    if assignment.due_date is not None:
        db_assignment.due_date = assignment.due_date
    
    if assignment.notes is not None:
        db_assignment.notes = assignment.notes
    
    db.commit()
    db.refresh(db_assignment)
    
    return db_assignment

@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    db_assignment = db.query(models.StepAssignment).filter(
        models.StepAssignment.id == assignment_id
    ).first()
    
    if db_assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(db_assignment)
    db.commit()
    
    return None

