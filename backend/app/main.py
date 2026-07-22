import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import complaints, dashboard
from app.models import (
    Complaint,
    Investigation,
    Capa,
    ComplaintStatus,
    ComplaintType,
    Severity,
    SourceType,
    InvestigationStatus,
)
from app.services.complaint_service import log_audit, generate_complaint_number
from datetime import date, datetime, timedelta


def seed_sample_data():
    db = SessionLocal()
    try:
        if db.query(Complaint).count() > 0:
            return

        samples = [
            {
                "source_type": SourceType.email,
                "customer_name": "MedSupply Distribution LLC",
                "product_name": "Acetaminophen API 500mg",
                "batch_lot_number": "API-2024-0892",
                "mfg_date": date(2024, 6, 15),
                "date_received": date(2024, 8, 2),
                "description": "Customer reported off-white discoloration in API batch API-2024-0892. Particle size appears inconsistent upon visual inspection.",
                "contact_info": "qa@medsupply.com",
                "complaint_type": ComplaintType.quality_defect,
                "severity": Severity.major,
                "classification_rationale": "Visual defect in API batch affecting product appearance; no safety signal but quality concern.",
                "status": ComplaintStatus.under_investigation,
                "assigned_to": "Dr. Sarah Chen — QA Lead",
            },
            {
                "source_type": SourceType.pdf,
                "customer_name": "Global Pharma Retail",
                "product_name": "Ibuprofen FDF 200mg Tablets",
                "batch_lot_number": "FDF-IBU-2024-0441",
                "mfg_date": date(2024, 5, 20),
                "date_received": date(2024, 7, 28),
                "description": "Mislabeled blister pack — expiry date printed as 2026 instead of 2025. Batch FDF-IBU-2024-0441.",
                "contact_info": "regulatory@gpharma.com",
                "complaint_type": ComplaintType.packaging_labeling,
                "severity": Severity.critical,
                "classification_rationale": "Labeling error with expiry date poses patient safety risk and potential regulatory reportability.",
                "regulatory_reportable": True,
                "status": ComplaintStatus.capa_in_progress,
                "assigned_to": "Maria Santos — Regulatory Affairs",
            },
            {
                "source_type": SourceType.manual,
                "customer_name": "Hospital Pharmacy Network",
                "product_name": "Metformin HCl FDF 850mg",
                "batch_lot_number": "FDF-MET-2024-0118",
                "mfg_date": date(2024, 4, 10),
                "date_received": date(2024, 7, 15),
                "description": "Patient reported gastrointestinal adverse event after taking Metformin from batch FDF-MET-2024-0118. Nausea and vomiting within 2 hours.",
                "contact_info": "pv@hpnetwork.org",
                "complaint_type": ComplaintType.adverse_event,
                "severity": Severity.critical,
                "classification_rationale": "Potential adverse drug reaction requiring pharmacovigilance assessment and possible MedWatch filing.",
                "regulatory_reportable": True,
                "status": ComplaintStatus.open_triaged,
                "assigned_to": "Dr. Raj Patel — QC Manager",
            },
        ]

        for s in samples:
            data = {k: v for k, v in s.items() if k != "status"}
            c = Complaint(complaint_number=generate_complaint_number(db), **data)
            c.status = s["status"]
            db.add(c)
            db.flush()
            db.add(Investigation(complaint_id=c.id, status=InvestigationStatus.pending))
            db.add(Capa(complaint_id=c.id))
            log_audit(db, c.id, "COMPLAINT_LOGGED", "seed", f"Seed data: {c.complaint_number}")

        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_sample_data()
    yield


settings = get_settings()

app = FastAPI(
    title="Pharma QMS — Customer Complaint Management",
    description="AI-powered complaint management for pharmaceutical API/FDF manufacturing",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pharma-qms-complaints"}


@app.get("/agents/graph")
def get_agent_graph():
    """Return LangGraph flow definition for UI visualization."""
    return {
        "intake_flow": [
            "Document Ingest",
            "Extraction Agent (gemma2-9b-it)",
            "Human Review/Edit Gate",
            "Classification Agent (gemma2-9b-it)",
            "Duplicate Detection Agent",
            "Log Complaint",
        ],
        "investigation_flow": [
            "Root Cause Agent (llama-3.3-70b-versatile)",
            "CAPA Recommendation Agent (llama-3.3-70b-versatile)",
            "Summary Agent (gemma2-9b-it)",
        ],
    }
