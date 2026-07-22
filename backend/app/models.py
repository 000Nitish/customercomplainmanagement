import enum
from datetime import datetime, date

from sqlalchemy import (
    String,
    Text,
    DateTime,
    Date,
    Float,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SourceType(str, enum.Enum):
    email = "email"
    pdf = "pdf"
    image = "image"
    manual = "manual"


class ComplaintType(str, enum.Enum):
    quality_defect = "quality_defect"
    packaging_labeling = "packaging_labeling"
    adverse_event = "adverse_event"
    counterfeit_suspicion = "counterfeit_suspicion"
    oos_related = "oos_related"
    unclassified = "unclassified"


class Severity(str, enum.Enum):
    critical = "Critical"
    major = "Major"
    minor = "Minor"


class ComplaintStatus(str, enum.Enum):
    draft = "Draft"
    open_triaged = "Open/Triaged"
    under_investigation = "Under Investigation"
    capa_in_progress = "CAPA In Progress"
    closed = "Closed"


class InvestigationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType))
    customer_name: Mapped[str | None] = mapped_column(String(255))
    product_name: Mapped[str | None] = mapped_column(String(255))
    batch_lot_number: Mapped[str | None] = mapped_column(String(128), index=True)
    mfg_date: Mapped[date | None] = mapped_column(Date)
    date_received: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(String(512))
    complaint_type: Mapped[ComplaintType | None] = mapped_column(SAEnum(ComplaintType))
    severity: Mapped[Severity | None] = mapped_column(SAEnum(Severity))
    classification_rationale: Mapped[str | None] = mapped_column(Text)
    regulatory_reportable: Mapped[bool | None] = mapped_column(default=False)
    risk_assessment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(ComplaintStatus), default=ComplaintStatus.draft
    )
    assigned_to: Mapped[str | None] = mapped_column(String(128))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    langgraph_state: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    documents: Mapped[list["ComplaintDocument"]] = relationship(back_populates="complaint")
    investigation: Mapped["Investigation | None"] = relationship(
        back_populates="complaint", uselist=False
    )
    capa: Mapped["Capa | None"] = relationship(back_populates="complaint", uselist=False)
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="complaint")


class ComplaintDocument(Base):
    __tablename__ = "complaint_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int | None] = mapped_column(ForeignKey("complaints.id"), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[float | None] = mapped_column(Float)

    complaint: Mapped["Complaint | None"] = relationship(back_populates="documents")


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), unique=True)
    root_cause: Mapped[str | None] = mapped_column(Text)
    root_cause_ai_suggestion: Mapped[str | None] = mapped_column(Text)
    clarifying_questions: Mapped[str | None] = mapped_column(Text)
    investigator_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[InvestigationStatus] = mapped_column(
        SAEnum(InvestigationStatus), default=InvestigationStatus.pending
    )

    complaint: Mapped["Complaint"] = relationship(back_populates="investigation")


class Capa(Base):
    __tablename__ = "capa"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), unique=True)
    corrective_action: Mapped[str | None] = mapped_column(Text)
    preventive_action: Mapped[str | None] = mapped_column(Text)
    ai_suggested: Mapped[bool] = mapped_column(default=False)
    effectiveness_check_date: Mapped[date | None] = mapped_column(Date)
    effectiveness_result: Mapped[str | None] = mapped_column(Text)

    complaint: Mapped["Complaint"] = relationship(back_populates="capa")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    action: Mapped[str] = mapped_column(String(128))
    actor: Mapped[str] = mapped_column(String(128), default="system")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    details: Mapped[str | None] = mapped_column(Text)

    complaint: Mapped["Complaint"] = relationship(back_populates="audit_logs")
