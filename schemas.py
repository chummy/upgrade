from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal

# User schemas
class UserBase(BaseModel):
    name: str
    email: str
    role: str
    specialty: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Patient schemas
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    external_id: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pathway Template schemas
class PathwayStepBase(BaseModel):
    name: str
    description: Optional[str] = None
    step_order: int
    step_type: str
    estimated_duration: Optional[int] = None
    required_roles: List[str] = []

class PathwayStepCreate(PathwayStepBase):
    pass

class PathwayStep(PathwayStepBase):
    id: int
    template_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PathwayTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    specialty: Optional[str] = None
    version: str = "1.0"
    status: str = "draft"

class PathwayTemplateCreate(PathwayTemplateBase):
    steps: List[PathwayStepCreate] = []
    created_by_id: Optional[int] = None

class PathwayTemplate(PathwayTemplateBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    steps: List[PathwayStep] = []

    class Config:
        from_attributes = True

# Care Team schemas
class CareTeamMemberBase(BaseModel):
    user_id: int
    role: str
    is_primary: bool = False

class CareTeamMemberCreate(CareTeamMemberBase):
    pass

class CareTeamMember(CareTeamMemberBase):
    id: int
    care_team_id: int
    created_at: datetime
    updated_at: datetime
    user: User

    class Config:
        from_attributes = True

class CareTeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    patient_id: int

class CareTeamCreate(CareTeamBase):
    members: List[CareTeamMemberCreate] = []

class CareTeam(CareTeamBase):
    id: int
    created_at: datetime
    updated_at: datetime
    members: List[CareTeamMember] = []
    patient: Patient

    class Config:
        from_attributes = True

# Step Assignment schemas
class StepAssignmentBase(BaseModel):
    pathway_id: int
    step_id: int
    assigned_to_id: int
    assigned_by_id: Optional[int] = None
    due_date: Optional[datetime] = None
    status: str = "pending"
    notes: Optional[str] = None

class StepAssignmentCreate(StepAssignmentBase):
    pass

class StepAssignmentUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class StepAssignment(StepAssignmentBase):
    id: int
    assigned_at: datetime
    pathway: "PatientPathway"
    step: PathwayStep
    assigned_to: User

    class Config:
        from_attributes = True

# Patient Pathway schemas
class CompletedStepBase(BaseModel):
    step_id: int
    completed_by: Optional[int] = None
    notes: Optional[str] = None

class CompletedStepCreate(CompletedStepBase):
    pass

class CompletedStep(CompletedStepBase):
    id: int
    pathway_id: int
    completed_at: datetime
    step: PathwayStep

    class Config:
        from_attributes = True

class PatientPathwayBase(BaseModel):
    patient_id: int
    template_id: int
    status: str = "active"

class PatientPathwayCreate(PatientPathwayBase):
    created_by_id: Optional[int] = None

class PatientPathwayUpdate(BaseModel):
    status: Optional[str] = None
    current_step_id: Optional[int] = None

class PatientPathway(PatientPathwayBase):
    id: int
    current_step_id: Optional[int] = None
    start_date: datetime
    estimated_end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    patient: Patient
    template: PathwayTemplate
    current_step: Optional[PathwayStep] = None
    completed_steps: List[CompletedStep] = []
    step_assignments: List[StepAssignment] = []

    class Config:
        from_attributes = True

# Notification schemas
class NotificationBase(BaseModel):
    title: str
    description: Optional[str] = None
    notification_type: str
    related_patient_id: Optional[int] = None
    related_pathway_id: Optional[int] = None
    priority: str = "normal"

class NotificationCreate(NotificationBase):
    recipient_id: Optional[int] = None

class Notification(NotificationBase):
    id: int
    recipient_id: Optional[int] = None
    status: str
    created_at: datetime
    read_at: Optional[datetime] = None
    related_patient: Optional[Patient] = None
    related_pathway: Optional[PatientPathway] = None

    class Config:
        from_attributes = True

# AI Insight schemas
class AIInsightBase(BaseModel):
    title: str
    description: Optional[str] = None
    insight_type: str
    related_patient_id: Optional[int] = None
    related_pathway_id: Optional[int] = None
    confidence: Decimal

class AIInsightCreate(AIInsightBase):
    context: Dict[str, Any] = {}

class AIInsightStatusUpdate(BaseModel):
    status: str
    user_id: Optional[int] = None

class AIInsight(AIInsightBase):
    id: int
    status: str
    created_at: datetime
    acted_on_at: Optional[datetime] = None
    acted_on_by: Optional[int] = None
    related_patient: Optional[Patient] = None
    related_pathway: Optional[PatientPathway] = None

    class Config:
        from_attributes = True

# Pagination schemas
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 50

class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int

class PaginatedPatients(BaseModel):
    patients: List[Patient]
    pagination: PaginationParams

class PaginatedPathways(BaseModel):
    pathways: List[PatientPathway]
    pagination: PaginationParams

# Response schemas
class StandardResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None

# Complete Step schema
class CompleteStepRequest(BaseModel):
    step_id: int
    completed_by_id: Optional[int] = None
    notes: Optional[str] = None

