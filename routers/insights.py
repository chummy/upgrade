from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from services.ai_orchestrator import ai_orchestrator

router = APIRouter()

@router.get("/", response_model=List[schemas.AIInsight])
def get_insights(
    patient_id: Optional[int] = None,
    pathway_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1),
    db: Session = Depends(get_db)
):
    # Build query
    query = db.query(models.AIInsight)
    
    # Apply filters
    if patient_id:
        query = query.filter(models.AIInsight.related_patient_id == patient_id)
    
    if pathway_id:
        query = query.filter(models.AIInsight.related_pathway_id == pathway_id)
    
    if status:
        query = query.filter(models.AIInsight.status == status)
    
    # Get insights
    insights = query.order_by(models.AIInsight.created_at.desc()).limit(limit).all()
    
    return insights

@router.post("/", response_model=schemas.AIInsight, status_code=201)
def generate_insight(insight: schemas.AIInsightCreate, db: Session = Depends(get_db)):
    try:
        return ai_orchestrator.generate_insight(db, insight)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")

@router.post("/{insight_id}/update-status", response_model=schemas.AIInsight)
def update_insight_status(insight_id: int, status_update: schemas.AIInsightStatusUpdate, db: Session = Depends(get_db)):
    try:
        return ai_orchestrator.update_insight_status(
            db, insight_id, status_update.status, status_update.user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update insight status: {str(e)}")
