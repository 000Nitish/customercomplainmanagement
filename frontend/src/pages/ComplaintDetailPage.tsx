import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchComplaint, setAgentFlag, appendAgentSteps, updateLocalComplaint } from '../store/currentComplaintSlice';
import { api } from '../api/client';

export default function ComplaintDetailPage() {
  const { id } = useParams<{ id: string }>();
  const dispatch = useDispatch<AppDispatch>();
  const { data, loading, agentSteps } = useSelector((s: RootState) => s.currentComplaint);
  const [auditLog, setAuditLog] = useState<Array<{ action: string; actor: string; timestamp: string; details?: string }>>([]);
  const [investigators, setInvestigators] = useState<string[]>([]);
  const [assignTo, setAssignTo] = useState('');
  const [rootCause, setRootCause] = useState('');
  const [notes, setNotes] = useState('');
  const [capaCorrective, setCapaCorrective] = useState('');
  const [capaPreventive, setCapaPreventive] = useState('');
  const [effectivenessDate, setEffectivenessDate] = useState('');
  const [effectivenessResult, setEffectivenessResult] = useState('');

  useEffect(() => {
    if (id) {
      dispatch(fetchComplaint(Number(id)));
      api.auditLog(Number(id)).then((data) => setAuditLog(data)).catch(() => {});
      api.investigators().then((data) => setInvestigators(data.investigators)).catch(() => {});
    }
  }, [id, dispatch]);

  useEffect(() => {
    if (data) {
      setRootCause(data.investigation?.root_cause || '');
      setNotes(data.investigation?.investigator_notes || '');
      setCapaCorrective(data.capa?.corrective_action || '');
      setCapaPreventive(data.capa?.preventive_action || '');
      setAssignTo(data.assigned_to || '');
      setEffectivenessDate(data.capa?.effectiveness_check_date || '');
      setEffectivenessResult(data.capa?.effectiveness_result || '');
    }
  }, [data]);

  const runRootCause = async () => {
    if (!id) return;
    dispatch(setAgentFlag({ key: 'rootCause', value: true }));
    try {
      const result = await api.rootCause(Number(id));
      dispatch(appendAgentSteps(result.agent_steps || []));
      dispatch(fetchComplaint(Number(id)));
    } finally {
      dispatch(setAgentFlag({ key: 'rootCause', value: false }));
    }
  };

  const runCapa = async () => {
    if (!id) return;
    dispatch(setAgentFlag({ key: 'capa', value: true }));
    try {
      const result = await api.capa(Number(id));
      dispatch(appendAgentSteps(result.agent_steps || []));
      dispatch(fetchComplaint(Number(id)));
    } finally {
      dispatch(setAgentFlag({ key: 'capa', value: false }));
    }
  };

  const runSummary = async () => {
    if (!id) return;
    dispatch(setAgentFlag({ key: 'summarizing', value: true }));
    try {
      const result = await api.summary(Number(id));
      dispatch(appendAgentSteps(result.agent_steps || []));
      dispatch(updateLocalComplaint({ ai_summary: result.summary || '' }));
    } finally {
      dispatch(setAgentFlag({ key: 'summarizing', value: false }));
    }
  };

  const assignInvestigator = async () => {
    if (!id || !assignTo) return;
    await api.updateStatus(Number(id), {
      status: 'Under Investigation',
      assigned_to: assignTo,
      actor: 'qa_manager',
    });
    dispatch(fetchComplaint(Number(id)));
  };

  const saveInvestigation = async () => {
    if (!id) return;
    await api.updateInvestigation(Number(id), {
      root_cause: rootCause,
      investigator_notes: notes,
      status: 'in_progress',
      actor: 'investigator',
    });
    dispatch(fetchComplaint(Number(id)));
  };

  const saveCapa = async () => {
    if (!id) return;
    await api.updateCapa(Number(id), {
      corrective_action: capaCorrective,
      preventive_action: capaPreventive,
      effectiveness_check_date: effectivenessDate || undefined,
      effectiveness_result: effectivenessResult || undefined,
      actor: 'investigator',
    });
    dispatch(fetchComplaint(Number(id)));
  };

  const closeComplaint = async () => {
    if (!id) return;
    await api.updateStatus(Number(id), { status: 'Closed', actor: 'investigator' });
    dispatch(fetchComplaint(Number(id)));
  };

  if (loading || !data) return <p>Loading complaint...</p>;

  const questions = (() => {
    const raw = data.investigation?.clarifying_questions;
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  })();

  return (
    <div>
      <div className="page-header">
        <h2>{data.complaint_number}</h2>
        <p>{data.product_name} — Batch {data.batch_lot_number} · <span className="badge badge-status">{data.status}</span></p>
      </div>

      {agentSteps.length > 0 && (
        <div className="agent-steps">
          {agentSteps.map((step, i) => (
            <span key={i} className="agent-step">{step}</span>
          ))}
        </div>
      )}

      {data.ai_summary && (
        <div className="card ai-panel">
          <div className="ai-label">AI Executive Summary</div>
          <p>{data.ai_summary}</p>
        </div>
      )}

      <div className="detail-grid">
        <div>
          <div className="card">
            <h3>Complaint Details</h3>
            <p><strong>Customer:</strong> {data.customer_name}</p>
            <p><strong>Source:</strong> {data.source_type}</p>
            <p><strong>Received:</strong> {data.date_received}</p>
            <p><strong>Type:</strong> {data.complaint_type?.replace(/_/g, ' ')}</p>
            <p><strong>Severity:</strong> {data.severity && <span className={`badge badge-${data.severity.toLowerCase()}`}>{data.severity}</span>}</p>
            {data.regulatory_reportable && (
              <div className="regulatory-flag">Regulatory reportability flagged</div>
            )}
            {data.classification_rationale && (
              <div className="ai-panel" style={{ marginTop: '0.75rem' }}>
                <div className="ai-label">Classification Rationale</div>
                <p>{data.classification_rationale}</p>
              </div>
            )}
            <p style={{ marginTop: '0.75rem' }}>{data.description}</p>
          </div>

          <div className="card">
            <h3>Investigation Assignment</h3>
            <div className="form-group">
              <label>Assign Investigator</label>
              <select value={assignTo} onChange={(e) => setAssignTo(e.target.value)}>
                <option value="">Select investigator...</option>
                {investigators.map((inv) => (
                  <option key={inv} value={inv}>{inv}</option>
                ))}
              </select>
            </div>
            <button className="btn btn-secondary" onClick={assignInvestigator} disabled={!assignTo}>
              Assign & Start Investigation
            </button>
          </div>

          <div className="card">
            <h3>Investigation & Root Cause Analysis</h3>
            <button className="btn btn-ai" onClick={runRootCause}>Run AI Root Cause Assistant</button>

            {data.investigation?.root_cause_ai_suggestion && (
              <div className="ai-panel">
                <div className="ai-label">AI-Suggested Root Cause</div>
                <p>{data.investigation.root_cause_ai_suggestion}</p>
                {questions.length > 0 && (
                  <>
                    <p style={{ marginTop: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}>Clarifying Questions:</p>
                    <ul>{questions.map((q: string, i: number) => <li key={i}>{q}</li>)}</ul>
                  </>
                )}
              </div>
            )}

            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label>Confirmed Root Cause (Human)</label>
              <textarea value={rootCause} onChange={(e) => setRootCause(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Investigator Notes</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <button className="btn btn-secondary" onClick={saveInvestigation}>Save Investigation</button>
          </div>

          <div className="card">
            <h3>CAPA (Corrective & Preventive Action)</h3>
            <button className="btn btn-ai" onClick={runCapa}>Run AI CAPA Recommendation</button>

            {data.capa?.ai_suggested && (
              <div className="ai-panel">
                <div className="ai-label">AI-Suggested CAPA</div>
                <p><strong>Corrective:</strong> {data.capa.corrective_action}</p>
                <p><strong>Preventive:</strong> {data.capa.preventive_action}</p>
              </div>
            )}

            <div className="form-group" style={{ marginTop: '1rem' }}>
              <label>Corrective Action (Human-Confirmed)</label>
              <textarea value={capaCorrective} onChange={(e) => setCapaCorrective(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Preventive Action (Human-Confirmed)</label>
              <textarea value={capaPreventive} onChange={(e) => setCapaPreventive(e.target.value)} />
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label>Effectiveness Check Date</label>
                <input type="date" value={effectivenessDate} onChange={(e) => setEffectivenessDate(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Effectiveness Result</label>
                <input value={effectivenessResult} onChange={(e) => setEffectivenessResult(e.target.value)} placeholder="Effective / Not effective" />
              </div>
            </div>
            <div className="actions-row">
              <button className="btn btn-secondary" onClick={saveCapa}>Save CAPA</button>
              <button className="btn btn-primary" onClick={closeComplaint}>Close Complaint</button>
            </div>
          </div>
        </div>

        <div>
          <div className="card">
            <h3>LangGraph Agent Flow</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Intake: Extract → Classify → Duplicate Check → Log<br />
              Investigation: Root Cause → CAPA → Summary
            </p>
            <button className="btn btn-ai" style={{ marginTop: '0.5rem' }} onClick={runSummary}>
              Generate Executive Summary
            </button>
          </div>

          <div className="card">
            <h3>Audit Trail</h3>
            <div className="timeline">
              {auditLog.map((entry) => (
                <div key={entry.timestamp + entry.action} className="timeline-item">
                  <div className="time">{new Date(entry.timestamp).toLocaleString()}</div>
                  <div className="action">{entry.action}</div>
                  <div style={{ fontSize: '0.8rem' }}>{entry.actor}{entry.details ? ` — ${entry.details}` : ''}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
