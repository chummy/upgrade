from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.CareTeam])
def get_care_teams(
    patient_id: int,
    db: Session = Depends(get_db)
):
    care_teams = db.query(models.CareTeam).filter(
        models.CareTeam.patient_id == patient_id
    ).all()
    
    return care_teams

@router.post("/", response_model=schemas.CareTeam, status_code=201)
def create_care_team(care_team: schemas.CareTeamCreate, db: Session = Depends(get_db)):
    # Create care team
    db_care_team = models.CareTeam(
        name=care_team.name,
        description=care_team.description,
        patient_id=care_team.patient_id
    )
    
    db.add(db_care_team)
    db.flush()  # Flush to get the care team ID
    
    # Add members if provided
    if care_team.members:
        for member in care_team.members:
            db_member = models.CareTeamMember(
                care_team_id=db_care_team.id,
                user_id=member.user_id,
                role=member.role,
                is_primary=member.is_primary
            )
            db.add(db_member)
    
    db.commit()
    db.refresh(db_care_team)
    
    return db_care_team

@router.get("/{care_team_id}", response_model=schemas.CareTeam)
def get_care_team(care_team_id: int, db: Session = Depends(get_db)):
    care_team = db.query(models.CareTeam).filter(
        models.CareTeam.id == care_team_id
    ).first()
    
    if care_team is None:
        raise HTTPException(status_code=404, detail="Care team not found")
    
    return care_team

@router.put("/{care_team_id}", response_model=schemas.CareTeam)
def update_care_team(care_team_id: int, care_team: schemas.CareTeamBase, db: Session = Depends(get_db)):
    db_care_team = db.query(models.CareTeam).filter(
        models.CareTeam.id == care_team_id
    ).first()
    
    if db_care_team is None:
        raise HTTPException(status_code=404, detail="Care team not found")
    
    # Update care team attributes
    db_care_team.name = care_team.name
    db_care_team.description = care_team.description
    
    db.commit()
    db.refresh(db_care_team)
    
    return db_care_team

@router.delete("/{care_team_id}", status_code=204)
def delete_care_team(care_team_id: int, db: Session = Depends(get_db)):
    db_care_team = db.query(models.CareTeam).filter(
        models.CareTeam.id == care_team_id
    ).first()
    
    if db_care_team is None:
        raise HTTPException(status_code=404, detail="Care team not found")
    
    db.delete(db_care_team)
    db.commit()
    
    return None

@router.get("/{care_team_id}/members", response_model=List[schemas.CareTeamMember])
def get_care_team_members(care_team_id: int, db: Session = Depends(get_db)):
    members = db.query(models.CareTeamMember).filter(
        models.CareTeamMember.care_team_id == care_team_id
    ).all()
    
    return members

@router.post("/{care_team_id}/members", response_model=schemas.CareTeamMember, status_code=201)
def add_care_team_member(care_team_id: int, member: schemas.CareTeamMemberCreate, db: Session = Depends(get_db)):
    # Check if care team exists
    care_team = db.query(models.CareTeam).filter(
        models.CareTeam.id == care_team_id
    ).first()
    
    if care_team is None:
        raise HTTPException(status_code=404, detail="Care team not found")
    
    # Check if user exists
    user = db.query(models.User).filter(
        models.User.id == member.user_id
    ).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if member already exists
    existing_member = db.query(models.CareTeamMember).filter(
        models.CareTeamMember.care_team_id == care_team_id,
        models.CareTeamMember.user_id == member.user_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of this care team")
    
    # Create member
    db_member = models.CareTeamMember(
        care_team_id=care_team_id,
        user_id=member.user_id,
        role=member.role,
        is_primary=member.is_primary
    )
    
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    
    return db_member

@router.delete("/{care_team_id}/members/{member_id}", status_code=204)
def remove_care_team_member(care_team_id: int, member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.CareTeamMember).filter(
        models.CareTeamMember.id == member_id,
        models.CareTeamMember.care_team_id == care_team_id
    ).first()
    
    if member is None:
        raise HTTPException(status_code=404, detail="Care team member not found")
    
    db.delete(member)
    db.commit()
    
    return None

