import { Link } from 'react-router-dom';
import Header from '../components/Header';
import StoragePointForm from '../components/StoragePointForm';
import { useLang } from '../lib/lang-context';
export default function PartnerPage() {
  const { t } = useLang();
  return <div className="search-page"><Header /><main className="search-main">
    <h1 className="search-title">{t.partnerDashboard}</h1>
    <nav className="partner-dashboard-actions" aria-label={t.partnerDashboard}>
      <Link className="partner-dashboard-button" to="/partner/storage-points">
        <span>{t.myStoragePoints}</span><span aria-hidden="true">→</span>
      </Link>
      <Link className="partner-dashboard-button" to="/partner/bookings">
        <span>{t.partnerBookings}</span><span aria-hidden="true">→</span>
      </Link>
    </nav>
    <StoragePointForm />
  </main></div>;
}
