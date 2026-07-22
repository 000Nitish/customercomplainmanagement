from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import (
    SourceType,
    ComplaintType,
    Severity,
    ComplaintStatus,
    InvestigationStatus,
)


class ExtractionResult(BaseModel):
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    mfg_date: Optional[date] = None
    date_received: Optional[date] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None
    extraction_confidence: float = 0.0
    extracted_text: Optional[str] = None
    source_type: SourceType = SourceType.manual
    agent_steps: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    complaint_type: ComplaintType
    severity: Severity
    rationale: str
    regulatory_reportable: bool = False
    risk_assessment: Optional[str] = None
    agent_steps: list[str] = Field(default_factory=list)


class RootCauseResult(BaseModel):
    root_cause_suggestion: str
    clarifying_questions: list[str] = Field(default_factory=list)
    agent_steps: list[str] = Field(default_factory=list)


class CapaResult(BaseModel):
    corrective_action: str
    preventive_action: str
    agent_steps: list[str] = Field(default_factory=list)


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool
    similar_complaint_ids: list[int] = Field(default_factory=list)
    rationale: str = ""


class CompletenessResult(BaseModel):
    is_complete: bool
    missing_fields: list[str] = Field(default_factory=list)


class ComplaintCreate(BaseModel):
    source_type: SourceType
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    mfg_date: Optional[date] = None
    date_received: Optional[date] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None
    complaint_type: Optional[ComplaintType] = None
    severity: Optional[Severity] = None
    classification_rationale: Optional[str] = None
    regulatory_reportable: Optional[bool] = False
    risk_assessment: Optional[str] = None
    actor: str = "user"


class ComplaintUpdate(BaseModel):
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    mfg_date: Optional[date] = None
    date_received: Optional[date] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None
    complaint_type: Optional[ComplaintType] = None
    severity: Optional[Severity] = None
    assigned_to: Optional[str] = None
    actor: str = "user"


class StatusUpdate(BaseModel):
    status: ComplaintStatus
    assigned_to: Optional[str] = None
    actor: str = "user"


class InvestigationUpdate(BaseModel):
    root_cause: Optional[str] = None
    investigator_notes: Optional[str] = None
    status: Optional[InvestigationStatus] = None
    actor: str = "user"


class CapaUpdate(BaseModel):
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    effectiveness_check_date: Optional[date] = None
    effectiveness_result: Optional[str] = None
    actor: str = "user"


class AuditLogOut(BaseModel):
    id: int
    action: str
    actor: str
    timestamp: datetime
    details: Optional[str] = None

    model_config = {"from_attributes": True}


class InvestigationOut(BaseModel):
    id: int
    root_cause: Optional[str] = None
    root_cause_ai_suggestion: Optional[str] = None
    clarifying_questions: Optional[str] = None
    investigator_notes: Optional[str] = None
    status: InvestigationStatus

    model_config = {"from_attributes": True}


class CapaOut(BaseModel):
    id: int
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    ai_suggested: bool
    effectiveness_check_date: Optional[date] = None
    effectiveness_result: Optional[str] = None

    model_config = {"from_attributes": True}


class ComplaintOut(BaseModel):
    id: int
    complaint_number: str
    source_type: SourceType
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    batch_lot_number: Optional[str] = None
    mfg_date: Optional[date] = None
    date_received: Optional[date] = None
    description: Optional[str] = None
    contact_info: Optional[str] = None
    complaint_type: Optional[ComplaintType] = None
    severity: Optional[Severity] = None
    classification_rationale: Optional[str] = None
    regulatory_reportable: Optional[bool] = None
    risk_assessment: Optional[str] = None
    status: ComplaintStatus
    assigned_to: Optional[str] = None
    ai_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    investigation: Optional[InvestigationOut] = None
    capa: Optional[CapaOut] = None

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total: int
    by_status: dict[str, int]
    by_severity: dict[str, int]
    by_product: dict[str, int]
    by_type: dict[str, int]
    recent_trend: list[dict]
