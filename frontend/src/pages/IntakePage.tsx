import { useState, ChangeEvent, FormEvent } from 'react';

interface IntakeFormState {
  source_type: string;
  customer_name: string;
  product_name: string;
  batch_lot_number: string;
  mfg_date: string;
  date_received: string;
  description: string;
  contact_info: string;
  complaint_type: string;
  severity: string;
  classification_rationale: string;
  regulatory_reportable: boolean;
  risk_assessment: string;
}
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { AppDispatch } from '../store';
import { api } from '../api/client';
import { setAgentFlag, appendAgentSteps, clearAgentSteps } from '../store/currentComplaintSlice';

export default function IntakePage() {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const [form, setForm] = useState<IntakeFormState>({
    source_type: 'pdf',
    customer_name: '',
    product_name: '',
    batch_lot_number: '',
    mfg_date: '',
    date_received: new Date().toISOString().slice(0, 10),
    description: '',
    contact_info: '',
    complaint_type: '',
    severity: '',
    classification_rationale: '',
    regulatory_reportable: false,
    risk_assessment: '',
  });
  const [agentSteps, setAgentSteps] = useState<string[]>([]);
  const [classification, setClassification] = useState<Record<string, unknown> | null>(null);
  const [duplicate, setDuplicate] = useState<Record<string, unknown> | null>(null);
  const [completeness, setCompleteness] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError('');
    dispatch(clearAgentSteps());
    dispatch(setAgentFlag({ key: 'extracting', value: true }));

    try {
      const result = await api.uploadDocument(file);
      setForm((f) => ({
        ...f,
        source_type: result.source_type || f.source_type,
        customer_name: result.customer_name || '',
        product_name: result.product_name || '',
        batch_lot_number: result.batch_lot_number || '',
        mfg_date: result.mfg_date || '',
        date_received: result.date_received || f.date_received,
        description: result.description || result.extracted_text || '',
        contact_info: result.contact_info || '',
      }));
      const steps = result.agent_steps || [];
      setAgentSteps(steps);
      dispatch(appendAgentSteps(steps));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
      dispatch(setAgentFlag({ key: 'extracting', value: false }));
    }
  };

  const runClassification = async () => {
    setLoading(true);
    setError('');
    dispatch(setAgentFlag({ key: 'classifying', value: true }));
    try {
      const preview = await api.intakePreview(form);
      const cls = preview.classification as Record<string, unknown>;
      setClassification(cls);
      setDuplicate(preview.duplicate_check as Record<string, unknown>);
      setCompleteness(preview.completeness as Record<string, unknown>);
      setForm((f) => ({
        ...f,
        complaint_type: (cls.complaint_type as string) || '',
        severity: (cls.severity as string) || '',
        classification_rationale: (cls.rationale as string) || '',
        regulatory_reportable: Boolean(cls.regulatory_reportable),
        risk_assessment: ((cls.risk_assessment as string) || ''),
      }));
      const steps = preview.agent_steps as string[];
      setAgentSteps((s) => [...s, ...steps]);
      dispatch(appendAgentSteps(steps));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Classification failed');
    } finally {
      setLoading(false);
      dispatch(setAgentFlag({ key: 'classifying', value: false }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (completeness && !(completeness as { is_complete: boolean }).is_complete) {
      setError('Please complete all required fields before logging the complaint.');
      return;
    }
    setLoading(true);
    try {
      const created = await api.createComplaint({ ...form, actor: 'intake_user' }) as { id: number };
      navigate(`/complaints/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Complaint Intake</h2>
        <p>Upload a complaint document (PDF, email, image) — AI extracts fields for human review before logging.</p>
      </div>

      <div className="card">
        <label className="upload-zone">
          <input type="file" accept=".pdf,.txt,.eml,.png,.jpg,.jpeg" onChange={handleUpload} />
          <p><strong>Drop or click to upload</strong> complaint source document</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>PDF, email text, or image</p>
        </label>
      </div>

      {agentSteps.length > 0 && (
        <div className="agent-steps">
          {agentSteps.map((step, i) => (
            <span key={i} className={`agent-step ${i === agentSteps.length - 1 ? 'active' : ''}`}>{step}</span>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <h3>Review Extracted Fields <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>(human-in-the-loop)</span></h3>
          <div className="form-grid">
            <div className="form-group">
              <label>Customer Name</label>
              <input value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Product Name (API/FDF)</label>
              <input value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Batch / Lot Number</label>
              <input value={form.batch_lot_number} onChange={(e) => setForm({ ...form, batch_lot_number: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Manufacturing Date</label>
              <input type="date" value={form.mfg_date} onChange={(e) => setForm({ ...form, mfg_date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Date Received</label>
              <input type="date" value={form.date_received} onChange={(e) => setForm({ ...form, date_received: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Contact Info</label>
              <input value={form.contact_info} onChange={(e) => setForm({ ...form, contact_info: e.target.value })} />
            </div>
            <div className="form-group full-width">
              <label>Complaint Description</label>
              <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>

          <div className="actions-row">
            <button type="button" className="btn btn-ai" onClick={runClassification} disabled={loading || !form.description}>
              Run AI Classification
            </button>
          </div>

          {classification && (
            <div className="ai-panel">
              <div className="ai-label">AI-Suggested Classification</div>
              <p><strong>Type:</strong> {(classification.complaint_type as string)?.replace(/_/g, ' ')}</p>
              <p><strong>Severity:</strong> {classification.severity as string}</p>
              <p><strong>Rationale:</strong> {classification.rationale as string}</p>
              {typeof classification.risk_assessment === 'string' && classification.risk_assessment && (
                <p><strong>Risk Assessment:</strong> {classification.risk_assessment}</p>
              )}
              {form.regulatory_reportable && (
                <div className="regulatory-flag">⚠ Regulatory reportability flagged — assess for Field Alert / MedWatch</div>
              )}
            </div>
          )}

          {duplicate && (duplicate as { is_duplicate: boolean }).is_duplicate && (
            <div className="ai-panel" style={{ borderColor: '#fbbf24', background: '#fffbeb' }}>
              <div className="ai-label" style={{ color: '#b45309' }}>Duplicate Detection</div>
              <p>{(duplicate as { rationale: string }).rationale}</p>
            </div>
          )}

          {completeness && !(completeness as { is_complete: boolean }).is_complete && (
            <div className="error-msg">
              Missing required fields: {(completeness as { missing_fields: string[] }).missing_fields.join(', ')}
            </div>
          )}
        </div>

        {error && <p className="error-msg">{error}</p>}

        <button type="submit" className="btn btn-primary" disabled={loading}>
          Log Complaint (Generate Complaint ID)
        </button>
      </form>
    </div>
  );
}
