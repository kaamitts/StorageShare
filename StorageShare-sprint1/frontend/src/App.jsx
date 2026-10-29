import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LangProvider } from './lib/LangContext';
import ProtectedRoute from './lib/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SearchPage from './pages/SearchPage';
import PartnerPage from './pages/PartnerPage';
import StorageDetailPage from './pages/StorageDetailPage';
export default function App() {
  return <LangProvider><BrowserRouter><Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route element={<ProtectedRoute />}>
      <Route path="/search" element={<SearchPage />} />
      <Route path="/storage/:id" element={<StorageDetailPage />} />
    </Route>
    <Route element={<ProtectedRoute role="partner" />}>
      <Route path="/partner" element={<PartnerPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/search" replace />} />
  </Routes></BrowserRouter></LangProvider>;
}
