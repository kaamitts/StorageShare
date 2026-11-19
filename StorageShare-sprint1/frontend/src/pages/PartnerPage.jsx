import { Link } from 'react-router-dom';
import Header from '../components/Header';
import StoragePointForm from '../components/StoragePointForm';
import { useLang } from '../lib/lang-context';
export default function PartnerPage() {
  const { t } = useLang();
  return <div className="search-page"><Header /><main className="search-main">
    <h1 className="search-title">{t.partnerDashboard}</h1>
    <Link className="btn-secondary" to="/partner/storage-points">{t.myStoragePoints}</Link>
    <Link className="btn-secondary" to="/partner/bookings">{t.partnerBookings}</Link>
    <StoragePointForm />
  </main></div>;
}
