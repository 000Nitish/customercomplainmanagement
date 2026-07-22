import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function ManualComplaintPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    source_type: 'manual',
    customer_name: '',
    product_name: '',
    batch_lot_number: '',
    mfg_date: '',
    date_received: new Date().toISOString().slice(0, 10),
    description: '',
    contact_info: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const preview = await api.intakePreview(form);
      const cls = preview.classification as Record<string, unknown>;
      const created = await api.createComplaint({
        ...form,
        complaint_type: cls.complaint_type,
        severity: cls.severity,
        classification_rationale: cls.rationale,
        regulatory_reportable: cls.regulatory_reportable,
        risk_assessment: cls.risk_assessment,
        actor: 'manual_entry',
      }) as { id: number };
      navigate(`/complaints/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create complaint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>New Manual Complaint</h2>
        <p>Log a phone or portal complaint manually — AI classification runs on submit.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="form-grid">
            <div className="form-group">
              <label>Customer Name *</label>
              <input required value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Product Name (API/FDF) *</label>
              <input required value={form.product_name} onChange={(e) => setForm({ ...form, product_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Batch / Lot Number *</label>
              <input required value={form.batch_lot_number} onChange={(e) => setForm({ ...form, batch_lot_number: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Manufacturing Date</label>
              <input type="date" value={form.mfg_date} onChange={(e) => setForm({ ...form, mfg_date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Date Received *</label>
              <input type="date" required value={form.date_received} onChange={(e) => setForm({ ...form, date_received: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Contact Info</label>
              <input value={form.contact_info} onChange={(e) => setForm({ ...form, contact_info: e.target.value })} />
            </div>
            <div className="form-group full-width">
              <label>Complaint Description *</label>
              <textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>
        </div>
        {error && <p className="error-msg">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          Create & Classify Complaint
        </button>
      </form>
    </div>
  );
}
