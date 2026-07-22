import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import IntakePage from './pages/IntakePage';
import ManualComplaintPage from './pages/ManualComplaintPage';
import ComplaintDetailPage from './pages/ComplaintDetailPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/intake" element={<IntakePage />} />
          <Route path="/new" element={<ManualComplaintPage />} />
          <Route path="/complaints/:id" element={<ComplaintDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
