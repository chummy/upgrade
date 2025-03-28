from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
import math

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedPatients)
def get_patients(
    query: Optional[str] = None,
    limit: int = Query(50, ge=1),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    
    # Build query
    db_query = db.query(models.Patient)
    
    # Apply search filter if provided
    if query:
        db_query = db_query.filter(
            (models.Patient.first_name.ilike(f"%{query}%")) |
            (models.Patient.last_name.ilike(f"%{query}%")) |
            (models.Patient.external_id.ilike(f"%{query}%"))
        )
    
    # Get total count
    total = db_query.count()
    
    # Apply pagination
    patients = db_query.order_by(models.Patient.last_name.asc()).offset(skip).limit(limit).all()
    
    return {
        "patients": patients,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit)
        }
    }

@router.post("/", response_model=schemas.Patient, status_code=201)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        external_id=patient.external_id,
        contact_phone=patient.contact_phone,
        contact_email=patient.contact_email,
        address=patient.address
    )
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient

@router.get("/{patient_id}", response_model=schemas.Patient)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return db_patient

@router.put("/{patient_id}", response_model=schemas.Patient)
def update_patient(patient_id: int, patient: schemas.PatientUpdate, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update patient attributes
    for key, value in patient.dict().items():
        setattr(db_patient, key, value)
    
    db.commit()
    db.refresh(db_patient)
    
    return db_patient

@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db.delete(db_patient)
    db.commit()
    
    return None
