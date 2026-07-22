import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Complaint,
    Investigation,
    Capa,
    AuditLog,
    ComplaintStatus,
    ComplaintType,
    Severity,
    InvestigationStatus,
    SourceType,
)
from app.schemas import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintOut,
    StatusUpdate,
    InvestigationUpdate,
    CapaUpdate,
    ExtractionResult,
    ClassificationResult,
    RootCauseResult,
    CapaResult,
    DuplicateCheckResult,
    CompletenessResult,
)
from app.services.complaint_service import (
    save_upload,
    extract_text_from_file,
    generate_complaint_number,
    log_audit,
    get_existing_complaints_context,
    complaint_to_agent_state,
    _parse_date,
)
from app.agents.graph import (
    run_extraction_only,
    run_classification_only,
    run_intake_pipeline,
    run_root_cause_only,
    run_capa_only,
    run_summary_only,
)

router = APIRouter(prefix="/complaints", tags=["complaints"])

MOCK_INVESTIGATORS = [
    "Dr. Sarah Chen — QA Lead",
    "James Okafor — Manufacturing QA",
    "Maria Santos — Regulatory Affairs",
    "Dr. Raj Patel — QC Manager",
]


@router.get("/investigators")
def list_investigators():
    return {"investigators": MOCK_INVESTIGATORS}


@router.post("/upload", response_model=ExtractionResult)
async def upload_complaint_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    file_path, source_type = save_upload(content, file.filename or "upload.txt")
    raw_text = extract_text_from_file(file_path, source_type)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from document")

    try:
        result = run_extraction_only(raw_text, source_type)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI extraction failed: {str(e)}")

    return ExtractionResult(
        customer_name=result.get("customer_name"),
        product_name=result.get("product_name"),
        batch_lot_number=result.get("batch_lot_number"),
        mfg_date=_parse_date(result.get("mfg_date")),
        date_received=_parse_date(result.get("date_received")),
        description=result.get("description"),
        contact_info=result.get("contact_info"),
        extraction_confidence=result.get("extraction_confidence", 0.0),
        extracted_text=raw_text,
        source_type=source_type,
        agent_steps=result.get("agent_steps", []),
    )


@router.post("/intake-preview")
def intake_preview(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """Run full intake LangGraph pipeline on manual/reviewed data (preview before save)."""
    raw_text = payload.description or ""
    context = get_existing_complaints_context(db, payload.product_name, payload.batch_lot_number)
    try:
        result = run_intake_pipeline(raw_text, payload.source_type, context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Intake pipeline failed: {str(e)}")

    dup = result.get("duplicate_check") or {}
    comp = result.get("completeness") or {}

    return {
        "extraction": {
            "customer_name": result.get("customer_name") or payload.customer_name,
            "product_name": result.get("product_name") or payload.product_name,
            "batch_lot_number": result.get("batch_lot_number") or payload.batch_lot_number,
            "description": result.get("description") or payload.description,
        },
        "classification": ClassificationResult(
            complaint_type=ComplaintType(result.get("complaint_type", "unclassified")),
            severity=Severity(result.get("severity", "Minor")),
            rationale=result.get("classification_rationale", ""),
            regulatory_reportable=result.get("regulatory_reportable", False),
            risk_assessment=result.get("risk_assessment"),
            agent_steps=result.get("agent_steps", []),
        ),
        "duplicate_check": DuplicateCheckResult(
            is_duplicate=dup.get("is_duplicate", False),
            similar_complaint_ids=dup.get("similar_complaint_ids", []),
            rationale=dup.get("rationale", ""),
        ),
        "completeness": CompletenessResult(
            is_complete=comp.get("is_complete", False),
            missing_fields=comp.get("missing_fields", []),
        ),
        "agent_steps": result.get("agent_steps", []),
    }


@router.post("", response_model=ComplaintOut, status_code=201)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    complaint = Complaint(
        complaint_number=generate_complaint_number(db),
        source_type=payload.source_type,
        customer_name=payload.customer_name,
        product_name=payload.product_name,
        batch_lot_number=payload.batch_lot_number,
        mfg_date=payload.mfg_date,
        date_received=payload.date_received or date.today(),
        description=payload.description,
        contact_info=payload.contact_info,
        complaint_type=payload.complaint_type,
        severity=payload.severity,
        classification_rationale=payload.classification_rationale,
        regulatory_reportable=payload.regulatory_reportable,
        risk_assessment=payload.risk_assessment,
        status=ComplaintStatus.open_triaged,
    )
    db.add(complaint)
    db.flush()

    investigation = Investigation(complaint_id=complaint.id, status=InvestigationStatus.pending)
    capa_record = Capa(complaint_id=complaint.id)
    db.add(investigation)
    db.add(capa_record)

    log_audit(
        db,
        complaint.id,
        "COMPLAINT_LOGGED",
        payload.actor,
        f"Complaint {complaint.complaint_number} logged via {payload.source_type.value}",
    )
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("", response_model=list[ComplaintOut])
def list_complaints(
    status: Optional[ComplaintStatus] = None,
    severity: Optional[Severity] = None,
    product: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Complaint).order_by(Complaint.created_at.desc())
    if status:
        query = query.filter(Complaint.status == status)
    if severity:
        query = query.filter(Complaint.severity == severity)
    if product:
        query = query.filter(Complaint.product_name.ilike(f"%{product}%"))
    return query.all()


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.patch("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    for field, value in payload.model_dump(exclude={"actor"}, exclude_none=True).items():
        setattr(complaint, field, value)

    log_audit(db, complaint.id, "COMPLAINT_UPDATED", payload.actor, "Fields updated by user")
    db.commit()
    db.refresh(complaint)
    return complaint


@router.post("/{complaint_id}/classify", response_model=ClassificationResult)
def classify_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    state = complaint_to_agent_state(complaint)
    try:
        result = run_classification_only(state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Classification failed: {str(e)}")

    complaint.complaint_type = ComplaintType(result.get("complaint_type", "unclassified"))
    complaint.severity = Severity(result.get("severity", "Minor"))
    complaint.classification_rationale = result.get("classification_rationale")
    complaint.regulatory_reportable = result.get("regulatory_reportable", False)
    complaint.risk_assessment = result.get("risk_assessment")

    log_audit(db, complaint.id, "AI_CLASSIFICATION", "system", result.get("classification_rationale", ""))
    db.commit()

    return ClassificationResult(
        complaint_type=complaint.complaint_type,
        severity=complaint.severity,
        rationale=complaint.classification_rationale or "",
        regulatory_reportable=complaint.regulatory_reportable or False,
        risk_assessment=complaint.risk_assessment,
        agent_steps=result.get("agent_steps", []),
    )


@router.post("/{complaint_id}/root-cause", response_model=RootCauseResult)
def root_cause_analysis(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    state = complaint_to_agent_state(complaint)
    try:
        result = run_root_cause_only(state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Root cause analysis failed: {str(e)}")

    if not complaint.investigation:
        inv = Investigation(complaint_id=complaint.id)
        db.add(inv)
        db.flush()
        complaint.investigation = inv

    complaint.investigation.root_cause_ai_suggestion = result.get("root_cause_suggestion")
    questions = result.get("clarifying_questions", [])
    complaint.investigation.clarifying_questions = json.dumps(questions)
    complaint.investigation.status = InvestigationStatus.in_progress
    complaint.status = ComplaintStatus.under_investigation

    log_audit(db, complaint.id, "AI_ROOT_CAUSE", "system", result.get("root_cause_suggestion", ""))
    db.commit()

    return RootCauseResult(
        root_cause_suggestion=result.get("root_cause_suggestion", ""),
        clarifying_questions=questions,
        agent_steps=result.get("agent_steps", []),
    )


@router.post("/{complaint_id}/capa", response_model=CapaResult)
def capa_recommendation(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    state = complaint_to_agent_state(complaint)
    if complaint.investigation and complaint.investigation.root_cause_ai_suggestion:
        state["root_cause_suggestion"] = complaint.investigation.root_cause_ai_suggestion

    context = get_existing_complaints_context(db, complaint.product_name, complaint.batch_lot_number)
    state["existing_complaints_context"] = context

    try:
        result = run_capa_only(state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CAPA recommendation failed: {str(e)}")

    if not complaint.capa:
        capa = Capa(complaint_id=complaint.id)
        db.add(capa)
        db.flush()
        complaint.capa = capa

    complaint.capa.corrective_action = result.get("corrective_action")
    complaint.capa.preventive_action = result.get("preventive_action")
    complaint.capa.ai_suggested = True
    complaint.status = ComplaintStatus.capa_in_progress

    log_audit(db, complaint.id, "AI_CAPA", "system", "CAPA recommendations generated")
    db.commit()

    return CapaResult(
        corrective_action=result.get("corrective_action", ""),
        preventive_action=result.get("preventive_action", ""),
        agent_steps=result.get("agent_steps", []),
    )


@router.post("/{complaint_id}/summary")
def generate_summary(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    state = complaint_to_agent_state(complaint)
    try:
        result = run_summary_only(state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Summary generation failed: {str(e)}")

    complaint.ai_summary = result.get("executive_summary")
    log_audit(db, complaint.id, "AI_SUMMARY", "system", "Executive summary generated")
    db.commit()

    return {"summary": complaint.ai_summary, "agent_steps": result.get("agent_steps", [])}


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(complaint_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_status = complaint.status
    complaint.status = payload.status
    if payload.assigned_to:
        complaint.assigned_to = payload.assigned_to

    log_audit(
        db,
        complaint.id,
        "STATUS_CHANGE",
        payload.actor,
        f"{old_status.value} → {payload.status.value}",
    )
    db.commit()
    db.refresh(complaint)
    return complaint


@router.patch("/{complaint_id}/investigation", response_model=ComplaintOut)
def update_investigation(complaint_id: int, payload: InvestigationUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if not complaint.investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")

    for field, value in payload.model_dump(exclude={"actor"}, exclude_none=True).items():
        setattr(complaint.investigation, field, value)

    log_audit(db, complaint.id, "INVESTIGATION_UPDATED", payload.actor)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.patch("/{complaint_id}/capa-record", response_model=ComplaintOut)
def update_capa_record(complaint_id: int, payload: CapaUpdate, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if not complaint.capa:
        raise HTTPException(status_code=404, detail="CAPA record not found")

    for field, value in payload.model_dump(exclude={"actor"}, exclude_none=True).items():
        setattr(complaint.capa, field, value)

    log_audit(db, complaint.id, "CAPA_UPDATED", payload.actor)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/{complaint_id}/audit-log")
def get_audit_log(complaint_id: int, db: Session = Depends(get_db)):
    from app.schemas import AuditLogOut

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.complaint_id == complaint_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return [AuditLogOut.model_validate(log) for log in logs]
