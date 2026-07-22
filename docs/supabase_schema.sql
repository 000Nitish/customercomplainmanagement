-- Pharma QMS schema for Supabase PostgreSQL
-- Run in: Supabase Dashboard → SQL Editor → New query → Run
-- Use this if Alembic migrations cannot connect from your machine.

-- Enums
DO $$ BEGIN
  CREATE TYPE sourcetype AS ENUM ('email', 'pdf', 'image', 'manual');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE complainttype AS ENUM (
    'quality_defect', 'packaging_labeling', 'adverse_event',
    'counterfeit_suspicion', 'oos_related', 'unclassified'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE severity AS ENUM ('Critical', 'Major', 'Minor');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE complaintstatus AS ENUM (
    'Draft', 'Open/Triaged', 'Under Investigation', 'CAPA In Progress', 'Closed'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE investigationstatus AS ENUM ('pending', 'in_progress', 'completed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Tables
CREATE TABLE IF NOT EXISTS complaints (
  id SERIAL PRIMARY KEY,
  complaint_number VARCHAR(32) NOT NULL UNIQUE,
  source_type sourcetype NOT NULL,
  customer_name VARCHAR(255),
  product_name VARCHAR(255),
  batch_lot_number VARCHAR(128),
  mfg_date DATE,
  date_received DATE,
  description TEXT,
  contact_info VARCHAR(512),
  complaint_type complainttype,
  severity severity,
  classification_rationale TEXT,
  regulatory_reportable BOOLEAN DEFAULT FALSE,
  risk_assessment TEXT,
  status complaintstatus NOT NULL DEFAULT 'Draft',
  assigned_to VARCHAR(128),
  ai_summary TEXT,
  langgraph_state TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_complaints_complaint_number ON complaints(complaint_number);
CREATE INDEX IF NOT EXISTS ix_complaints_batch_lot_number ON complaints(batch_lot_number);

CREATE TABLE IF NOT EXISTS complaint_documents (
  id SERIAL PRIMARY KEY,
  complaint_id INTEGER REFERENCES complaints(id) ON DELETE CASCADE,
  file_path VARCHAR(512) NOT NULL,
  extracted_text TEXT,
  extraction_confidence DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS investigations (
  id SERIAL PRIMARY KEY,
  complaint_id INTEGER NOT NULL UNIQUE REFERENCES complaints(id) ON DELETE CASCADE,
  root_cause TEXT,
  root_cause_ai_suggestion TEXT,
  clarifying_questions TEXT,
  investigator_notes TEXT,
  status investigationstatus NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS capa (
  id SERIAL PRIMARY KEY,
  complaint_id INTEGER NOT NULL UNIQUE REFERENCES complaints(id) ON DELETE CASCADE,
  corrective_action TEXT,
  preventive_action TEXT,
  ai_suggested BOOLEAN NOT NULL DEFAULT FALSE,
  effectiveness_check_date DATE,
  effectiveness_result TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  complaint_id INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
  action VARCHAR(128) NOT NULL,
  actor VARCHAR(128) NOT NULL DEFAULT 'system',
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  details TEXT
);

CREATE INDEX IF NOT EXISTS ix_audit_log_complaint_id ON audit_log(complaint_id);

-- Auto-update updated_at on complaints
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS complaints_updated_at ON complaints;
CREATE TRIGGER complaints_updated_at
  BEFORE UPDATE ON complaints
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (optional — enable when adding Supabase Auth)
-- ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
