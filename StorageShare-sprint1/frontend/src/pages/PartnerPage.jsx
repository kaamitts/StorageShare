import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { useLang } from '../lib/lang-context';
export default function PartnerPage() {
  const { t } = useLang();
  return <div className="search-page"><Header /><main className="search-main">
    <h1>{t.partnerDashboard}</h1><p>{t.partnerPlaceholder}</p><Link to="/search">{t.findStorage}</Link>
  </main></div>;
}
