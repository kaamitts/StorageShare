import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LangProvider } from './lib/LangContext';
import ProtectedRoute from './lib/AuthContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SearchPage from './pages/SearchPage';
import PartnerPage from './pages/PartnerPage';
import PartnerBookingsPage from './pages/PartnerBookingsPage';
import CheckInPage from './pages/CheckInPage';
import StorageDetailPage from './pages/StorageDetailPage';
import HistoryPage from './pages/HistoryPage';
import MyStoragePointsPage from './pages/MyStoragePointsPage';
import DemoPaymentPage from './pages/DemoPaymentPage';
import PendingPaymentPage from './pages/PendingPaymentPage';
import ProfilePage from './pages/ProfilePage';
import { ThemeProvider } from './lib/ThemeContext';
export default function App() {
  return <ThemeProvider><LangProvider><BrowserRouter><Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route element={<ProtectedRoute />}>
      <Route path="/search" element={<SearchPage />} />
      <Route path="/storage/:id" element={<StorageDetailPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route element={<ProtectedRoute role="traveler" />}>
        <Route path="/pending-payment" element={<PendingPaymentPage />} />
      </Route>
      <Route path="/demo-payment" element={<DemoPaymentPage />} />
    </Route>
    <Route element={<ProtectedRoute role="partner" />}>
      <Route path="/partner" element={<PartnerPage />} />
      <Route path="/partner/storage-points" element={<MyStoragePointsPage />} />
      <Route path="/partner/bookings" element={<PartnerBookingsPage />} />
      <Route path="/partner/check-in/:token" element={<CheckInPage />} />
      <Route path="/checkin/:token" element={<CheckInPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/search" replace />} />
  </Routes></BrowserRouter></LangProvider></ThemeProvider>;
}
