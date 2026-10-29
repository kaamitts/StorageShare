import { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { getStoragePointById } from '../api/storage';
import { useLang } from '../lib/lang-context';
import { districtName } from '../lib/districts';
import Header from '../components/Header';
export default function StorageDetailPage() {
  const { id } = useParams();
  // Remount the loader when navigating between detail URLs.
  return <Detail key={id} id={id} />;
}
function Detail({ id }) {
  const { lang, t } = useLang(); const [params] = useSearchParams();
  const [result, setResult] = useState({ loading: true }); const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getStoragePointById(id, controller.signal).then(point => setResult({ point }))
      .catch(error => { if (error.name !== 'AbortError') setResult({ error }); });
    return () => controller.abort();
  }, [id, attempt]);
  const p = result.point;
  const district = params.get('district');
  return <div className="search-page"><Header /><main className="search-main">
    <Link className="back-btn" to={`/search${district ? `?district=${encodeURIComponent(district)}` : ''}`}>{t.backToList}</Link>
    {result.loading ? <p>{t.loading}</p> : result.error ? <div role="alert">{result.error.status === 404 ? t.notFound : t.requestError}
      {result.error.status !== 404 && <button onClick={() => { setResult({ loading: true }); setAttempt(a => a + 1); }}>{t.retry}</button>}</div> :
      <div className="detail-card"><h1 className="detail-name">{p.name}</h1><div className="detail-rows">
        {[[t.district, districtName(p.district_code, lang, p.district)], [t.address, p.address],
          [t.price, `${p.price_per_bag_per_hour} ₸ ${t.perBagPerHour}`], [t.hours, `${p.opens_at} – ${p.closes_at}`],
          ...(p.security_notes ? [[t.security, p.security_notes]] : [])].map(([label, value]) =>
          <div className="detail-row" key={label}><span className="detail-label">{label}</span><span className="detail-value">{value}</span></div>)}
      </div></div>}
  </main></div>;
}
