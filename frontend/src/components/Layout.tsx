import { NavLink, Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>Pharma QMS</h1>
        <p className="subtitle">Customer Complaint Management</p>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/intake">Complaint Intake</NavLink>
          <NavLink to="/new">Manual Complaint</NavLink>
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
