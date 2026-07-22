const API_BASE = import.meta.env.VITE_API_URL || '/api';

type ApiErrorMessage = { detail?: string };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }) as ApiErrorMessage);
    throw new Error(err.detail || 'Request failed');
  }
  return res.json() as Promise<T>;
}

export const api = {
  getComplaints: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<Complaint[]>(`/complaints${qs}`);
  },
  getComplaint: (id: number) => request<Complaint>(`/complaints/${id}`),
  createComplaint: (data: unknown) =>
    request<Complaint>('/complaints', { method: 'POST', body: JSON.stringify(data) }),
  updateComplaint: (id: number, data: unknown) =>
    request<Complaint>(`/complaints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateStatus: (id: number, data: unknown) =>
    request<Complaint>(`/complaints/${id}/status`, { method: 'PATCH', body: JSON.stringify(data) }),
  uploadDocument: async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/complaints/upload`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Upload failed');
    return res.json() as Promise<{
      customer_name?: string;
      product_name?: string;
      batch_lot_number?: string;
      mfg_date?: string;
      date_received?: string;
      description?: string;
      contact_info?: string;
      extracted_text?: string;
      source_type?: string;
      agent_steps?: string[];
    }>;
  },
  intakePreview: (data: unknown) =>
    request<{
      classification: Record<string, unknown>;
      duplicate_check: Record<string, unknown>;
      completeness: Record<string, unknown>;
      agent_steps: string[];
    }>('/complaints/intake-preview', { method: 'POST', body: JSON.stringify(data) }),
  classify: (id: number) =>
    request<{ complaint_type?: string; severity?: string; rationale?: string; regulatory_reportable?: boolean; risk_assessment?: string; agent_steps?: string[] }>(`/complaints/${id}/classify`, { method: 'POST' }),
  rootCause: (id: number) =>
    request<{ root_cause_suggestion?: string; clarifying_questions?: string[]; agent_steps?: string[] }>(`/complaints/${id}/root-cause`, { method: 'POST' }),
  capa: (id: number) =>
    request<{ corrective_action?: string; preventive_action?: string; agent_steps?: string[] }>(`/complaints/${id}/capa`, { method: 'POST' }),
  summary: (id: number) =>
    request<{ summary?: string; agent_steps?: string[] }>(`/complaints/${id}/summary`, { method: 'POST' }),
  updateInvestigation: (id: number, data: unknown) =>
    request<Complaint>(`/complaints/${id}/investigation`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateCapa: (id: number, data: unknown) =>
    request<Complaint>(`/complaints/${id}/capa-record`, { method: 'PATCH', body: JSON.stringify(data) }),
  auditLog: (id: number) => request<Array<{ action: string; actor: string; timestamp: string; details?: string }>>(`/complaints/${id}/audit-log`),
  dashboard: () => request<{ total: number; by_status: Record<string, number>; by_severity: Record<string, number>; by_product: Record<string, number>; by_type: Record<string, number>; recent_trend: Array<{ period: string; count: number }> }>('/dashboard/summary'),
  investigators: () => request<{ investigators: string[] }>('/complaints/investigators'),
  agentGraph: () => request<{ intake_flow: string[]; investigation_flow: string[] }>('/agents/graph'),
};

export type Complaint = {
  id: number;
  complaint_number: string;
  source_type: string;
  customer_name?: string;
  product_name?: string;
  batch_lot_number?: string;
  mfg_date?: string;
  date_received?: string;
  description?: string;
  contact_info?: string;
  complaint_type?: string;
  severity?: string;
  classification_rationale?: string;
  regulatory_reportable?: boolean;
  risk_assessment?: string;
  status: string;
  assigned_to?: string;
  ai_summary?: string;
  created_at: string;
  updated_at: string;
  investigation?: {
    root_cause?: string;
    root_cause_ai_suggestion?: string;
    clarifying_questions?: string;
    investigator_notes?: string;
    status: string;
  };
  capa?: {
    corrective_action?: string;
    preventive_action?: string;
    ai_suggested: boolean;
    effectiveness_check_date?: string;
    effectiveness_result?: string;
  };
};
