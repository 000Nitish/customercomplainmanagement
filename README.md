# Pharma QMS — AI-Powered Customer Complaint Management System

A pharmaceutical Quality Management System (QMS) module for managing customer complaints related to **API (Active Pharmaceutical Ingredient)** and **FDF (Finished Dosage Form)** manufacturing. Built with LangGraph agent orchestration, FastAPI, React + Redux, and a Supabase PostgreSQL backend for deployment.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     React + Redux Frontend                       │
│  Dashboard │ Intake │ Manual Form │ Complaint Detail │ Audit    │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                             │
│  /complaints/*  │  /dashboard/*  │  /agents/graph                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   LangGraph Agent Orchestration                  │
│                                                                  │
│  INTAKE FLOW:                                                    │
│  [Document Ingest] → [Extraction] → [Human Review Gate]          │
│       → [Classification] → [Duplicate Detection] → [Log]         │
│                                                                  │
│  INVESTIGATION FLOW (on-demand):                                │
│  [Root Cause Agent] → [CAPA Agent] → [Summary Agent]             │
│                                                                  │
│  Models: gemma2-9b-it (fast) │ llama-3.3-70b-versatile (RCA)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     PostgreSQL Database                          │
│  complaints │ investigations │ capa │ audit_log │ documents    │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Redux Toolkit, Vite, React Router |
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| AI | LangGraph, LangChain-Groq |
| LLMs | `gemma2-9b-it`, `llama-3.3-70b-versatile` |
| Database | Supabase PostgreSQL |
| Font | Google Inter |

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (or a Supabase Postgres connection string)
- Groq API key ([console.groq.com](https://console.groq.com)) for live LLM calls; the app also runs in demo mode without it

## Setup

### 1. Clone and configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your GROQ_API_KEY and Supabase DATABASE_URL
```

### 2. Database

```bash
# Create PostgreSQL database (or use your Supabase connection string)
createdb pharma_qms

# Run migrations
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for live LLM calls; leave empty to use local demo heuristics |
| `DATABASE_URL` | PostgreSQL connection string (can point to Supabase) |
| `SUPABASE_DATABASE_URL` | Optional alternative for Supabase deployments |
| `FRONTEND_URL` | CORS origin (default: http://localhost:5173) |
| `UPLOAD_DIR` | Directory for uploaded complaint documents |

## Core Workflow

1. **Intake** — Upload PDF/email/image or manual form entry
2. **AI Extraction** — LangGraph extraction agent pre-fills structured fields
3. **Human Review** — User confirms/edits extracted data
4. **AI Classification** — Type, severity, regulatory reportability with rationale
5. **Complaint Logged** — Unique Complaint ID generated, audit trail entry
6. **Investigation Assignment** — Assign to investigator, status → Under Investigation
7. **AI Root Cause** — 5-Whys/fishbone-style RCA suggestions
8. **AI CAPA** — Corrective/preventive action recommendations
9. **Closure** — Human-confirmed root cause + CAPA, effectiveness check, status → Closed
10. **Dashboard** — Kanban, filters, product trend view

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/complaints/upload` | Upload document, run extraction agent |
| POST | `/complaints/intake-preview` | Full intake LangGraph pipeline preview |
| POST | `/complaints` | Save confirmed complaint |
| GET | `/complaints` | List complaints (filterable) |
| GET | `/complaints/{id}` | Complaint detail |
| POST | `/complaints/{id}/classify` | Run classification agent |
| POST | `/complaints/{id}/root-cause` | Run root cause agent |
| POST | `/complaints/{id}/capa` | Run CAPA recommendation agent |
| POST | `/complaints/{id}/summary` | Generate executive summary |
| PATCH | `/complaints/{id}/status` | Update status + audit log |
| GET | `/complaints/{id}/audit-log` | QMS audit trail |
| GET | `/dashboard/summary` | Dashboard counts and trends |
| GET | `/agents/graph` | LangGraph flow definition |

## Bonus AI Features

- **Duplicate Complaint Detection** — Compares new complaints against existing product/batch records
- **Completeness Checker** — Flags missing required fields before submission
- **AI Risk Classification** — Patient/regulatory risk assessment with rationale
- **Executive Summary Agent** — One-paragraph summary for complaint detail view

## Seed Data

Sample complaint documents are in `/seed_data/`:

- `complaint_email_acetaminophen_api.txt` — API quality defect
- `complaint_email_ibuprofen_labeling.txt` — Critical labeling error
- `complaint_adverse_event_metformin.txt` — Adverse event / pharmacovigilance
- `complaint_oos_amoxicillin_api.txt` — OOS-related API complaint
- `complaint_phone_atorvastatin.txt` — Manual phone intake example

The backend also seeds 3 sample complaints in the database on first startup.

## Project Structure

```
/frontend          React + Redux Toolkit + Vite
/backend           FastAPI + LangGraph + SQLAlchemy
  /app
    /agents        LangGraph graph definitions
    /routers       API route handlers
    /services      Business logic
    models.py      SQLAlchemy ORM models
    schemas.py     Pydantic request/response models
  /alembic         Database migrations
/docs              Architecture documentation
/seed_data         Sample complaint documents
```

## Design Decisions

- **Human-in-the-loop**: All AI outputs are labeled "AI-suggested" and require human confirmation before becoming official QMS records (21 CFR Part 11 alignment).
- **Dual LLM strategy**: Fast model (`gemma2-9b-it`) for extraction/classification; reasoning model (`llama-3.3-70b-versatile`) for RCA and CAPA.
- **Immutable audit trail**: Every status change and AI agent run writes to `audit_log`.
- **LangGraph visibility**: Agent steps are returned to the frontend and displayed as a progress trail.

## License

MIT
