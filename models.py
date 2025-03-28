from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, 
    Table, Text, ARRAY, JSON, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    specialty = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    created_pathway_templates = relationship("PathwayTemplate", back_populates="created_by")
    created_patient_pathways = relationship("PatientPathway", back_populates="created_by")
    completed_steps = relationship("CompletedStep", back_populates="completed_by")
    notifications = relationship("Notification", back_populates="recipient")
    acted_on_insights = relationship("AIInsight", back_populates="acted_on_by")
    care_team_memberships = relationship("CareTeamMember", back_populates="user")
    step_assignments = relationship("StepAssignment", back_populates="assigned_to")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String)
    contact_phone = Column(String)
    contact_email = Column(String)
    address = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pathways = relationship("PatientPathway", back_populates="patient")
    notifications = relationship("Notification", back_populates="related_patient")
    ai_insights = relationship("AIInsight", back_populates="related_patient")
    care_teams = relationship("CareTeam", back_populates="patient")


class PathwayTemplate(Base):
    __tablename__ = "pathway_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    specialty = Column(String)
    version = Column(String, nullable=False)
    status = Column(String, default="draft")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="created_pathway_templates")
    steps = relationship("PathwayStep", back_populates="template")
    patient_pathways = relationship("PatientPathway", back_populates="template")


class PathwayStep(Base):
    __tablename__ = "pathway_steps"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("pathway_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False)
    estimated_duration = Column(Integer)
    required_roles = Column(ARRAY(String))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    template = relationship("PathwayTemplate", back_populates="steps")
    dependent_steps = relationship("StepDependency", foreign_keys="StepDependency.step_id", back_populates="step")
    dependency_for_steps = relationship("StepDependency", foreign_keys="StepDependency.dependency_step_id", back_populates="dependency_step")
    decision_points = relationship("DecisionPoint", foreign_keys="DecisionPoint.step_id", back_populates="step")
    true_decisions = relationship("DecisionPoint", foreign_keys="DecisionPoint.true_step_id", back_populates="true_step")
    false_decisions = relationship("DecisionPoint", foreign_keys="DecisionPoint.false_step_id", back_populates="false_step")
    current_for_pathways = relationship("PatientPathway", back_populates="current_step")
    completed_in_pathways = relationship("CompletedStep", back_populates="step")
    assignments = relationship("StepAssignment", back_populates="step")


class StepDependency(Base):
    __tablename__ = "step_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("pathway_steps.id", ondelete="CASCADE"), nullable=False)
    dependency_step_id = Column(Integer, ForeignKey("pathway_steps.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    step = relationship("PathwayStep", foreign_keys=[step_id], back_populates="dependent_steps")
    dependency_step = relationship("PathwayStep", foreign_keys=[dependency_step_id], back_populates="dependency_for_steps")


class DecisionPoint(Base):
    __tablename__ = "decision_points"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("pathway_steps.id", ondelete="CASCADE"), nullable=False)
    condition_expression = Column(String, nullable=False)
    true_step_id = Column(Integer, ForeignKey("pathway_steps.id", ondelete="SET NULL"))
    false_step_id = Column(Integer, ForeignKey("pathway_steps.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    step = relationship("PathwayStep", foreign_keys=[step_id], back_populates="decision_points")
    true_step = relationship("PathwayStep", foreign_keys=[true_step_id], back_populates="true_decisions")
    false_step = relationship("PathwayStep", foreign_keys=[false_step_id], back_populates="false_decisions")


class PatientPathway(Base):
    __tablename__ = "patient_pathways"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("pathway_templates.id"), nullable=False)
    current_step_id = Column(Integer, ForeignKey("pathway_steps.id"))
    status = Column(String, default="active")
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    estimated_end_date = Column(DateTime(timezone=True))
    actual_end_date = Column(DateTime(timezone=True))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="pathways")
    template = relationship("PathwayTemplate", back_populates="patient_pathways")
    current_step = relationship("PathwayStep", back_populates="current_for_pathways")
    created_by_user = relationship("User", back_populates="created_patient_pathways")
    completed_steps = relationship("CompletedStep", back_populates="pathway")
    notifications = relationship("Notification", back_populates="related_pathway")
    ai_insights = relationship("AIInsight", back_populates="related_pathway")
    step_assignments = relationship("StepAssignment", back_populates="pathway")


class CompletedStep(Base):
    __tablename__ = "completed_steps"

    id = Column(Integer, primary_key=True, index=True)
    pathway_id = Column(Integer, ForeignKey("patient_pathways.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, ForeignKey("pathway_steps.id"), nullable=False)
    completed_by = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(String)

    # Relationships
    pathway = relationship("PatientPathway", back_populates="completed_steps")
    step = relationship("PathwayStep", back_populates="completed_in_pathways")
    completed_by_user = relationship("User", back_populates="completed_steps")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(String)
    notification_type = Column(String, nullable=False)
    related_patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"))
    related_pathway_id = Column(Integer, ForeignKey("patient_pathways.id", ondelete="SET NULL"))
    priority = Column(String, default="normal")
    status = Column(String, default="unread")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))

    # Relationships
    recipient = relationship("User", back_populates="notifications")
    related_patient = relationship("Patient", back_populates="notifications")
    related_pathway = relationship("PatientPathway", back_populates="notifications")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(String, nullable=False)
    data = Column(JSON, nullable=False)
    event_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    insight_type = Column(String, nullable=False)
    related_patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"))
    related_pathway_id = Column(Integer, ForeignKey("patient_pathways.id", ondelete="SET NULL"))
    confidence = Column(Numeric(5, 4), nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    acted_on_at = Column(DateTime(timezone=True))
    acted_on_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    related_patient = relationship("Patient", back_populates="ai_insights")
    related_pathway = relationship("PatientPathway", back_populates="ai_insights")
    acted_on_by_user = relationship("User", back_populates="acted_on_insights")


class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    system_type = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    auth_type = Column(String, nullable=False)
    auth_config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    mappings = Column(JSON)
    transformations = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    requests = relationship("IntegrationRequest", back_populates="config")


class IntegrationRequest(Base):
    __tablename__ = "integration_requests"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("integration_configs.id"), nullable=False)
    operation = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending")
    result = Column(JSON)
    error = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    config = relationship("IntegrationConfig", back_populates="requests")


# New models for care teams and assignments

class CareTeam(Base):
    __tablename__ = "care_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="care_teams")
    members = relationship("CareTeamMember", back_populates="care_team")


class CareTeamMember(Base):
    __tablename__ = "care_team_members"

    id = Column(Integer, primary_key=True, index=True)
    care_team_id = Column(Integer, ForeignKey("care_teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    care_team = relationship("CareTeam", back_populates="members")
    user = relationship("User", back_populates="care_team_memberships")


class StepAssignment(Base):
    __tablename__ = "step_assignments"

    id = Column(Integer, primary_key=True, index=True)
    pathway_id = Column(Integer, ForeignKey("patient_pathways.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(Integer, ForeignKey("pathway_steps.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    status = Column(String, default="pending")
    notes = Column(String)

    # Relationships
    pathway = relationship("PatientPathway", back_populates="step_assignments")
    step = relationship("PathwayStep", back_populates="assignments")
    assigned_to = relationship("User", back_populates="step_assignments")

