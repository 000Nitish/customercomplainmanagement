import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { AppDispatch, RootState } from '../store';
import { fetchComplaints } from '../store/complaintsSlice';
import { fetchDashboard } from '../store/dashboardSlice';

const STATUS_ORDER = ['Open/Triaged', 'Under Investigation', 'CAPA In Progress', 'Closed', 'Draft'];

function severityClass(s?: string) {
  if (!s) return 'badge-status';
  return `badge badge-${s.toLowerCase()}`;
}

export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>();
  const { items, loading } = useSelector((s: RootState) => s.complaints);
  const { summary } = useSelector((s: RootState) => s.dashboard);

  useEffect(() => {
    dispatch(fetchComplaints());
    dispatch(fetchDashboard());
  }, [dispatch]);

  const byStatus = STATUS_ORDER.reduce<Record<string, typeof items>>((acc, st) => {
    acc[st] = items.filter((c) => c.status === st);
    return acc;
  }, {});

  return (
    <div>
      <div className="page-header">
        <h2>Complaint Dashboard</h2>
        <p>Monitor customer complaints across API and FDF products — triage, investigate, and trend.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="value">{summary?.total ?? '—'}</div>
          <div className="label">Total Complaints</div>
        </div>
        <div className="stat-card">
          <div className="value">{summary?.by_severity?.Critical ?? 0}</div>
          <div className="label">Critical</div>
        </div>
        <div className="stat-card">
          <div className="value">{summary?.by_severity?.Major ?? 0}</div>
          <div className="label">Major</div>
        </div>
        <div className="stat-card">
          <div className="value">{Object.keys(summary?.by_product ?? {}).length}</div>
          <div className="label">Products Affected</div>
        </div>
      </div>

      <div className="card">
        <h3>Kanban by Status</h3>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <div className="kanban">
            {STATUS_ORDER.map((status) => (
              <div key={status} className="kanban-col">
                <h4>{status} ({byStatus[status]?.length ?? 0})</h4>
                {(byStatus[status] ?? []).map((c) => (
                  <Link key={c.id} to={`/complaints/${c.id}`} className="kanban-card">
                    <strong>{c.complaint_number}</strong>
                    <div>{c.product_name}</div>
                    <div>Lot: {c.batch_lot_number}</div>
                    {c.severity && <span className={severityClass(c.severity)}>{c.severity}</span>}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3>All Complaints</h3>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Product</th>
              <th>Batch/Lot</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Assigned To</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/complaints/${c.id}`}>{c.complaint_number}</Link></td>
                <td>{c.product_name}</td>
                <td>{c.batch_lot_number}</td>
                <td>{c.complaint_type?.replace(/_/g, ' ')}</td>
                <td>{c.severity && <span className={severityClass(c.severity)}>{c.severity}</span>}</td>
                <td><span className="badge badge-status">{c.status}</span></td>
                <td>{c.assigned_to ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {summary && Object.keys(summary.by_product).length > 0 && (
        <div className="card">
          <h3>Complaints by Product (Trend View)</h3>
          <table>
            <thead>
              <tr><th>Product</th><th>Count</th></tr>
            </thead>
            <tbody>
              {Object.entries(summary.by_product)
                .sort(([, a], [, b]) => b - a)
                .map(([product, count]) => (
                  <tr key={product}><td>{product}</td><td>{count}</td></tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
