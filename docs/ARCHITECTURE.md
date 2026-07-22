# Architecture Documentation

## LangGraph Agent Flow

```mermaid
graph TD
    A[Document Ingest] --> B[Extraction Agent<br/>gemma2-9b-it]
    B --> C[Human Review/Edit Gate]
    C --> D[Classification Agent<br/>gemma2-9b-it]
    D --> E[Duplicate Detection Agent<br/>gemma2-9b-it]
    E --> F[Completeness Checker]
    F --> G[Log Complaint]

    G -.->|On-demand from UI| H[Root Cause Agent<br/>llama-3.3-70b-versatile]
    H --> I[CAPA Recommendation Agent<br/>llama-3.3-70b-versatile]
    I --> J[Summary Agent<br/>gemma2-9b-it]
```

## Data Model Relationships

```mermaid
erDiagram
    complaints ||--o{ complaint_documents : has
    complaints ||--o| investigations : has
    complaints ||--o| capa : has
    complaints ||--o{ audit_log : tracks

    complaints {
        int id PK
        string complaint_number UK
        enum source_type
        string product_name
        string batch_lot_number
        enum complaint_type
        enum severity
        enum status
        string assigned_to
    }

    investigations {
        int id PK
        int complaint_id FK
        text root_cause
        text root_cause_ai_suggestion
        enum status
    }

    capa {
        int id PK
        int complaint_id FK
        text corrective_action
        text preventive_action
        date effectiveness_check_date
    }

    audit_log {
        int id PK
        int complaint_id FK
        string action
        string actor
        datetime timestamp
    }
```

## State Persistence

LangGraph intermediate outputs are persisted via:
1. **Complaint record fields** — classification, severity, rationale stored on the complaint
2. **Investigation/CAPA records** — AI suggestions stored separately from human-confirmed values
3. **Audit log** — Every agent invocation logged with timestamp and actor
4. **`langgraph_state` JSON column** — Reserved for full graph state serialization on re-runs

## LLM Model Selection

| Agent | Model | Rationale |
|-------|-------|-----------|
| Extraction | gemma2-9b-it | Fast structured field parsing |
| Classification | gemma2-9b-it | Quick categorization with rationale |
| Duplicate Detection | gemma2-9b-it | Comparison against existing records |
| Root Cause Analysis | llama-3.3-70b-versatile | Deep reasoning, 5-Whys methodology |
| CAPA Recommendation | llama-3.3-70b-versatile | Complex corrective/preventive planning |
| Executive Summary | gemma2-9b-it | Concise narrative generation |

## Frontend Redux Slices

| Slice | Purpose |
|-------|---------|
| `complaints` | List view, filters, kanban data |
| `currentComplaint` | Detail view, agent run flags, draft intake form |
| `dashboard` | Summary counts, trend data |

Agent status flags in `currentComplaint`: `extracting`, `classifying`, `rootCause`, `capa`, `summarizing`
