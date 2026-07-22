import json
import re
from typing import TypedDict, Annotated, Optional
from datetime import date

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.config import get_settings
from app.models import ComplaintType, Severity, SourceType


class ComplaintGraphState(TypedDict, total=False):
    raw_text: str
    source_type: str
    customer_name: Optional[str]
    product_name: Optional[str]
    batch_lot_number: Optional[str]
    mfg_date: Optional[str]
    date_received: Optional[str]
    description: Optional[str]
    contact_info: Optional[str]
    extraction_confidence: float
    complaint_type: Optional[str]
    severity: Optional[str]
    classification_rationale: Optional[str]
    regulatory_reportable: bool
    risk_assessment: Optional[str]
    root_cause_suggestion: Optional[str]
    clarifying_questions: list[str]
    corrective_action: Optional[str]
    preventive_action: Optional[str]
    executive_summary: Optional[str]
    duplicate_check: Optional[dict]
    completeness: Optional[dict]
    agent_steps: Annotated[list[str], lambda a, b: a + b]
    existing_complaints_context: str


def _get_fast_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model="gemma2-9b-it",
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
    )


def _get_reasoning_llm() -> ChatGroq:
    settings = get_settings()
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=settings.groq_api_key,
        temperature=0.2,
    )


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def document_ingest_node(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "agent_steps": [f"Document Ingest: received {state.get('source_type', 'unknown')} source"],
    }


def _fallback_extraction(state: ComplaintGraphState) -> ComplaintGraphState:
    raw_text = (state.get("raw_text") or "").strip()
    lower_text = raw_text.lower()

    product = "Unspecified product"
    if "acetaminophen" in lower_text:
        product = "Acetaminophen API 500mg"
    elif "ibuprofen" in lower_text:
        product = "Ibuprofen FDF 200mg Tablets"
    elif "metformin" in lower_text:
        product = "Metformin HCl FDF 850mg"

    batch = None
    for token in re.findall(r"[A-Z0-9-]{2,}", raw_text):
        if "API" in token or "FDF" in token or "LOT" in token or "BATCH" in token:
            continue
        if len(token) >= 4:
            batch = token
            break

    description = raw_text[:1200] if raw_text else "Complaint received through the QMS intake workflow."
    return {
        "customer_name": "Demo Customer",
        "product_name": product,
        "batch_lot_number": batch,
        "mfg_date": str(date.today().replace(day=1).isoformat()),
        "date_received": str(date.today().isoformat()),
        "description": description,
        "contact_info": "qa@example.com",
        "extraction_confidence": 0.74,
        "agent_steps": ["Extraction Agent: demo-mode heuristic extraction engaged"],
    }


def _fallback_classification(state: ComplaintGraphState) -> ComplaintGraphState:
    text = f"{state.get('product_name', '')} {state.get('description', '')}".lower()
    complaint_type = ComplaintType.quality_defect.value
    severity = Severity.major.value
    if "label" in text or "expiry" in text:
        complaint_type = ComplaintType.packaging_labeling.value
        severity = Severity.critical.value
    elif "adverse" in text or "patient" in text:
        complaint_type = ComplaintType.adverse_event.value
        severity = Severity.critical.value
    elif "oos" in text or "out of specification" in text:
        complaint_type = ComplaintType.oos_related.value
    rationale = "Demo-mode classification used a rule-based review to triage the complaint for the assessment workflow."
    return {
        "complaint_type": complaint_type,
        "severity": severity,
        "classification_rationale": rationale,
        "regulatory_reportable": "medwatch" in text or "field alert" in text or "adverse" in text,
        "risk_assessment": "Potential patient safety or regulatory exposure; review in the investigation workflow.",
        "agent_steps": ["Classification Agent: demo-mode classification applied"],
    }


def _fallback_duplicate(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "duplicate_check": {
            "is_duplicate": False,
            "similar_complaint_ids": [],
            "rationale": "No duplicate match identified in demo mode.",
        },
        "agent_steps": ["Duplicate Detection Agent: demo-mode duplicate check applied"],
    }


def _fallback_root_cause(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "root_cause_suggestion": "Demo root-cause suggestion: review batch records, line clearance, and packaging controls for the reported defect pattern.",
        "clarifying_questions": [
            "Was the issue observed on a single lot or multiple lots?",
            "Did the defect appear before or after packaging?",
        ],
        "agent_steps": ["Root Cause Agent: demo-mode RCA applied"],
    }


def _fallback_capa(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "corrective_action": "Quarantine the implicated batch and perform targeted inspection before release.",
        "preventive_action": "Update the control plan and add a review checkpoint to reduce recurrence.",
        "agent_steps": ["CAPA Recommendation Agent: demo-mode CAPA suggested"],
    }


def _fallback_summary(state: ComplaintGraphState) -> ComplaintGraphState:
    return {
        "executive_summary": "The complaint was logged through the AI-assisted QMS workflow and routed to investigation for human review.",
        "agent_steps": ["Summary Agent: demo-mode executive summary generated"],
    }


def extraction_agent_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_fast_llm()
        prompt = f"""You are a pharmaceutical QMS data extraction agent. Extract structured fields from this customer complaint document.

Return ONLY valid JSON with these keys:
- customer_name (string or null)
- product_name (string or null) — include API or FDF designation if mentioned
- batch_lot_number (string or null)
- mfg_date (YYYY-MM-DD or null)
- date_received (YYYY-MM-DD or null)
- description (string — full complaint narrative)
- contact_info (string or null)
- extraction_confidence (float 0-1)

Document text:
{state.get('raw_text', '')[:8000]}
"""
        response = llm.invoke([SystemMessage(content="Extract pharma complaint fields. JSON only."), HumanMessage(content=prompt)])
        data = _parse_json_response(response.content)
        return {
            "customer_name": data.get("customer_name"),
            "product_name": data.get("product_name"),
            "batch_lot_number": data.get("batch_lot_number"),
            "mfg_date": data.get("mfg_date"),
            "date_received": data.get("date_received"),
            "description": data.get("description"),
            "contact_info": data.get("contact_info"),
            "extraction_confidence": float(data.get("extraction_confidence", 0.75)),
            "agent_steps": ["Extraction Agent: structured fields extracted from document"],
        }
    except Exception:
        return _fallback_extraction(state)


def classification_agent_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_fast_llm()
        prompt = f"""Classify this pharmaceutical customer complaint for a QMS system.

Complaint details:
- Product: {state.get('product_name')}
- Batch/Lot: {state.get('batch_lot_number')}
- Description: {state.get('description')}

Return ONLY valid JSON:
- complaint_type: one of [quality_defect, packaging_labeling, adverse_event, counterfeit_suspicion, oos_related]
- severity: one of [Critical, Major, Minor]
- rationale: string explaining classification (2-3 sentences)
- regulatory_reportable: boolean (true if potential Field Alert / MedWatch / serious adverse event)
- risk_assessment: string describing patient/regulatory risk
"""
        response = llm.invoke([SystemMessage(content="Pharma QMS classifier. JSON only."), HumanMessage(content=prompt)])
        data = _parse_json_response(response.content)
        return {
            "complaint_type": data.get("complaint_type", ComplaintType.unclassified.value),
            "severity": data.get("severity", Severity.minor.value),
            "classification_rationale": data.get("rationale", ""),
            "regulatory_reportable": bool(data.get("regulatory_reportable", False)),
            "risk_assessment": data.get("risk_assessment"),
            "agent_steps": ["Classification Agent: type and severity assigned with rationale"],
        }
    except Exception:
        return _fallback_classification(state)


def duplicate_detection_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_fast_llm()
        context = state.get("existing_complaints_context", "No existing complaints.")
        prompt = f"""Check if this new complaint may be a duplicate of existing complaints.

New complaint:
- Product: {state.get('product_name')}
- Batch: {state.get('batch_lot_number')}
- Description: {state.get('description')}

Existing complaints:
{context[:4000]}

Return ONLY valid JSON:
- is_duplicate: boolean
- similar_complaint_ids: list of integer IDs (empty if none)
- rationale: string
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        data = _parse_json_response(response.content)
        return {
            "duplicate_check": data,
            "agent_steps": ["Duplicate Detection Agent: compared against existing complaints"],
        }
    except Exception:
        return _fallback_duplicate(state)


def completeness_checker_node(state: ComplaintGraphState) -> ComplaintGraphState:
    required = {
        "customer_name": state.get("customer_name"),
        "product_name": state.get("product_name"),
        "batch_lot_number": state.get("batch_lot_number"),
        "date_received": state.get("date_received"),
        "description": state.get("description"),
    }
    missing = [k for k, v in required.items() if not v]
    return {
        "completeness": {"is_complete": len(missing) == 0, "missing_fields": missing},
        "agent_steps": [f"Completeness Checker: {'passed' if not missing else 'missing ' + ', '.join(missing)}"],
    }


def root_cause_agent_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_reasoning_llm()
        prompt = f"""You are a pharma QMS root cause analysis assistant. Use 5-Whys / fishbone-style reasoning.

Complaint:
- Product: {state.get('product_name')} (API or FDF)
- Batch/Lot: {state.get('batch_lot_number')}
- Type: {state.get('complaint_type')}
- Severity: {state.get('severity')}
- Description: {state.get('description')}

Return ONLY valid JSON:
- root_cause_suggestion: string (probable root cause with reasoning)
- clarifying_questions: list of 2-4 questions for the investigator
"""
        response = llm.invoke([SystemMessage(content="Pharma RCA expert. JSON only."), HumanMessage(content=prompt)])
        data = _parse_json_response(response.content)
        return {
            "root_cause_suggestion": data.get("root_cause_suggestion", ""),
            "clarifying_questions": data.get("clarifying_questions", []),
            "agent_steps": ["Root Cause Agent: RCA suggestion generated (llama-3.3-70b)"],
        }
    except Exception:
        return _fallback_root_cause(state)


def capa_recommendation_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_reasoning_llm()
        prompt = f"""Recommend CAPA (Corrective and Preventive Actions) for this pharma complaint.

Product: {state.get('product_name')}
Batch: {state.get('batch_lot_number')}
Root cause context: {state.get('root_cause_suggestion', 'Not yet determined')}
Complaint: {state.get('description')}
Historical context: {state.get('existing_complaints_context', 'None')[:2000]}

Return ONLY valid JSON:
- corrective_action: string (immediate correction for this batch/issue)
- preventive_action: string (systemic prevention)
"""
        response = llm.invoke([SystemMessage(content="Pharma CAPA expert. JSON only."), HumanMessage(content=prompt)])
        data = _parse_json_response(response.content)
        return {
            "corrective_action": data.get("corrective_action", ""),
            "preventive_action": data.get("preventive_action", ""),
            "agent_steps": ["CAPA Recommendation Agent: corrective/preventive actions suggested (llama-3.3-70b)"],
        }
    except Exception:
        return _fallback_capa(state)


def summary_agent_node(state: ComplaintGraphState) -> ComplaintGraphState:
    try:
        llm = _get_fast_llm()
        prompt = f"""Write a one-paragraph executive summary for this pharma QMS complaint record.

Customer: {state.get('customer_name')}
Product: {state.get('product_name')} | Batch: {state.get('batch_lot_number')}
Type: {state.get('complaint_type')} | Severity: {state.get('severity')}
Status narrative: {state.get('description')}
Root cause: {state.get('root_cause_suggestion', 'Under investigation')}

Return plain text summary only, no JSON.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        return {
            "executive_summary": response.content.strip(),
            "agent_steps": ["Summary Agent: executive summary generated"],
        }
    except Exception:
        return _fallback_summary(state)


def build_intake_graph() -> StateGraph:
    """Intake flow: ingest → extract → classify → duplicate → completeness."""
    graph = StateGraph(ComplaintGraphState)
    graph.add_node("document_ingest", document_ingest_node)
    graph.add_node("extraction", extraction_agent_node)
    graph.add_node("classification", classification_agent_node)
    graph.add_node("duplicate_detection", duplicate_detection_node)
    graph.add_node("completeness_check", completeness_checker_node)

    graph.set_entry_point("document_ingest")
    graph.add_edge("document_ingest", "extraction")
    graph.add_edge("extraction", "classification")
    graph.add_edge("classification", "duplicate_detection")
    graph.add_edge("duplicate_detection", "completeness_check")
    graph.add_edge("completeness_check", END)
    return graph


def build_investigation_graph() -> StateGraph:
    """Investigation flow: root cause → CAPA → summary."""
    graph = StateGraph(ComplaintGraphState)
    graph.add_node("root_cause", root_cause_agent_node)
    graph.add_node("capa", capa_recommendation_node)
    graph.add_node("summary", summary_agent_node)

    graph.set_entry_point("root_cause")
    graph.add_edge("root_cause", "capa")
    graph.add_edge("capa", "summary")
    graph.add_edge("summary", END)
    return graph


intake_graph = build_intake_graph().compile()
investigation_graph = build_investigation_graph().compile()


def run_extraction_only(raw_text: str, source_type: SourceType) -> dict:
    state: ComplaintGraphState = {
        "raw_text": raw_text,
        "source_type": source_type.value,
        "agent_steps": [],
    }
    for node in ["document_ingest", "extraction"]:
        fn = {"document_ingest": document_ingest_node, "extraction": extraction_agent_node}[node]
        updates = fn(state)
        state.update(updates)
        state["agent_steps"] = state.get("agent_steps", []) + updates.get("agent_steps", [])
    return dict(state)


def run_classification_only(state_data: dict) -> dict:
    state: ComplaintGraphState = {**state_data, "agent_steps": []}
    updates = classification_agent_node(state)
    state.update(updates)
    return dict(state)


def run_intake_pipeline(raw_text: str, source_type: SourceType, existing_context: str = "") -> dict:
    state: ComplaintGraphState = {
        "raw_text": raw_text,
        "source_type": source_type.value,
        "existing_complaints_context": existing_context,
        "agent_steps": [],
    }
    result = intake_graph.invoke(state)
    return dict(result)


def run_root_cause_only(state_data: dict) -> dict:
    state: ComplaintGraphState = {**state_data, "agent_steps": []}
    updates = root_cause_agent_node(state)
    state.update(updates)
    return dict(state)


def run_capa_only(state_data: dict) -> dict:
    state: ComplaintGraphState = {**state_data, "agent_steps": []}
    updates = capa_recommendation_node(state)
    state.update(updates)
    return dict(state)


def run_summary_only(state_data: dict) -> dict:
    state: ComplaintGraphState = {**state_data, "agent_steps": []}
    updates = summary_agent_node(state)
    state.update(updates)
    return dict(state)
