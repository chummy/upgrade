import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from services.pathway_engine import pathway_engine
import math

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedPathways)
def get_pathways(
    status: Optional[str] = None,
    patient_id: Optional[int] = None,
    limit: int = Query(50, ge=1),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    
    # Build query
    query = db.query(models.PatientPathway)
    
    # Apply filters
    if status:
        query = query.filter(models.PatientPathway.status == status)
    
    if patient_id:
        query = query.filter(models.PatientPathway.patient_id == patient_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    pathways = query.order_by(models.PatientPathway.updated_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "pathways": pathways,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit)
        }
    }

@router.post("/", response_model=schemas.PatientPathway, status_code=201)
def create_pathway(pathway: schemas.PatientPathwayCreate, db: Session = Depends(get_db)):
    try:
        return pathway_engine.initialize_pathway(db, pathway)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pathway: {str(e)}")

@router.get("/{pathway_id}", response_model=schemas.PatientPathway)
def get_pathway(pathway_id: int, db: Session = Depends(get_db)):
    pathway = pathway_engine.get_patient_pathway(db, pathway_id)
    
    if pathway is None:
        raise HTTPException(status_code=404, detail="Pathway not found")
    
    return pathway

@router.put("/{pathway_id}", response_model=schemas.PatientPathway)
def update_pathway(pathway_id: int, pathway_update: schemas.PatientPathwayUpdate, db: Session = Depends(get_db)):
    db_pathway = db.query(models.PatientPathway).filter(models.PatientPathway.id == pathway_id).first()
    
    if db_pathway is None:
        raise HTTPException(status_code=404, detail="Pathway not found")
    
    # Only allow updating status and currentStepId
    if pathway_update.status is not None:
        db_pathway.status = pathway_update.status
    
    if pathway_update.current_step_id is not None:
        db_pathway.current_step_id = pathway_update.current_step_id
    
    db_pathway.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_pathway)
    
    return db_pathway

@router.post("/{pathway_id}/complete-step", response_model=schemas.PatientPathway)
def complete_step(pathway_id: int, step_data: schemas.CompleteStepRequest, db: Session = Depends(get_db)):
    try:
        return pathway_engine.complete_step(db, pathway_id, step_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete step: {str(e)}")
