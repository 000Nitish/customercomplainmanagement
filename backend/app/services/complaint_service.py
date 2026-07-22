import os
import uuid
from datetime import datetime, date
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    Complaint,
    ComplaintDocument,
    Investigation,
    Capa,
    AuditLog,
    ComplaintStatus,
    ComplaintType,
    Severity,
    InvestigationStatus,
    SourceType,
)
from app.agents.graph import (
    run_extraction_only,
    run_classification_only,
    run_intake_pipeline,
    run_root_cause_only,
    run_capa_only,
    run_summary_only,
)


def ensure_upload_dir() -> Path:
    settings = get_settings()
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_text_from_file(file_path: str, source_type: SourceType) -> str:
    if source_type == SourceType.pdf:
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if source_type in (SourceType.email, SourceType.manual):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return f"[Image document: {os.path.basename(file_path)} — OCR placeholder for demo]"


def generate_complaint_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Complaint).filter(Complaint.complaint_number.like(f"CC-{year}-%")).count()
    return f"CC-{year}-{count + 1:04d}"


def log_audit(db: Session, complaint_id: int, action: str, actor: str, details: str = ""):
    entry = AuditLog(complaint_id=complaint_id, action=action, actor=actor, details=details)
    db.add(entry)


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def save_upload(file_bytes: bytes, filename: str) -> tuple[str, SourceType]:
    upload_dir = ensure_upload_dir()
    ext = Path(filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / unique_name
    file_path.write_bytes(file_bytes)

    if ext == ".pdf":
        source = SourceType.pdf
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        source = SourceType.image
    elif ext in (".txt", ".eml"):
        source = SourceType.email
    else:
        source = SourceType.manual

    return str(file_path), source


def get_existing_complaints_context(db: Session, product_name: str | None, batch: str | None) -> str:
    query = db.query(Complaint)
    if product_name:
        query = query.filter(Complaint.product_name.ilike(f"%{product_name}%"))
    complaints = query.limit(20).all()
    lines = []
    for c in complaints:
        lines.append(
            f"ID={c.id} #{c.complaint_number} product={c.product_name} batch={c.batch_lot_number} "
            f"type={c.complaint_type} desc={ (c.description or '')[:200]}"
        )
    return "\n".join(lines) if lines else "No matching historical complaints."


def complaint_to_agent_state(complaint: Complaint) -> dict:
    return {
        "customer_name": complaint.customer_name,
        "product_name": complaint.product_name,
        "batch_lot_number": complaint.batch_lot_number,
        "mfg_date": str(complaint.mfg_date) if complaint.mfg_date else None,
        "date_received": str(complaint.date_received) if complaint.date_received else None,
        "description": complaint.description,
        "contact_info": complaint.contact_info,
        "complaint_type": complaint.complaint_type.value if complaint.complaint_type else None,
        "severity": complaint.severity.value if complaint.severity else None,
        "root_cause_suggestion": (
            complaint.investigation.root_cause_ai_suggestion if complaint.investigation else None
        ),
    }
