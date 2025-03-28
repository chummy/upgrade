from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.PathwayTemplate])
def get_templates(
    specialty: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.PathwayTemplate)
    
    # Apply filters
    if specialty:
        query = query.filter(models.PathwayTemplate.specialty == specialty)
    
    if status:
        query = query.filter(models.PathwayTemplate.status == status)
    
    # Get templates with steps
    templates = query.order_by(models.PathwayTemplate.name.asc()).all()
    
    return templates

@router.post("/", response_model=schemas.PathwayTemplate, status_code=201)
def create_template(template: schemas.PathwayTemplateCreate, db: Session = Depends(get_db)):
    try:
        # Start a transaction
        # Create template
        db_template = models.PathwayTemplate(
            name=template.name,
            description=template.description,
            specialty=template.specialty,
            version=template.version,
            status=template.status,
            created_by=template.created_by_id
        )
        
        db.add(db_template)
        db.flush()  # Flush to get the template ID
        
        # Create steps
        if template.steps:
            for i, step in enumerate(template.steps):
                db_step = models.PathwayStep(
                    template_id=db_template.id,
                    name=step.name,
                    description=step.description,
                    step_order=i + 1,
                    step_type=step.step_type,
                    estimated_duration=step.estimated_duration,
                    required_roles=step.required_roles or []
                )
                db.add(db_step)
        
        db.commit()
        db.refresh(db_template)
        
        # Fetch the complete template with steps
        complete_template = db.query(models.PathwayTemplate).filter(
            models.PathwayTemplate.id == db_template.id
        ).first()
        
        return complete_template
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")

@router.get("/{template_id}", response_model=schemas.PathwayTemplate)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.PathwayTemplate).filter(
        models.PathwayTemplate.id == template_id
    ).first()
    
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template
