import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getDistricts, getStoragePoints } from '../api/storage';
import { useLang } from '../lib/lang-context';
import { districtName } from '../lib/districts';
import Header from '../components/Header';
export default function SearchPage() {
  const { lang, t } = useLang();
  const [params, setParams] = useSearchParams(); const district = params.get('district') || '';
  const [result, setResult] = useState({ districts: [], points: [], loading: true, error: false });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([getDistricts(controller.signal), getStoragePoints(district, controller.signal)])
      .then(([districts, points]) => setResult({ districts, points, loading: false, error: false }))
      .catch(error => { if (error.name !== 'AbortError') setResult(v => ({ ...v, loading: false, error: true })); });
    return () => controller.abort();
  }, [district, attempt]);
  function choose(value) { setResult(v => ({ ...v, loading: true, error: false })); setParams(value ? { district: value } : {}); }
  return <div className="search-page"><Header /><main className="search-main">
    <h1 className="search-title">{t.findStorage}</h1>
    <select aria-label={t.district} className="district-select" value={district} onChange={e => choose(e.target.value)}>
      <option value="">{t.allDistricts}</option>
      {result.districts.map(d => <option key={d.code} value={d.code}>{districtName(d.code, lang, d.name)}</option>)}
    </select>
    {result.loading ? <p>{t.loading}</p> : result.error ? <div role="alert">{t.requestError} <button onClick={() => { setResult(v => ({ ...v, loading: true })); setAttempt(a => a + 1); }}>{t.retry}</button></div> : result.points.length === 0 ? <p className="search-empty">{t.noPoints}</p> :
      <div className="cards-grid">{result.points.map(p => <Link className="card" key={p.id} to={`/storage/${p.id}${district ? `?district=${district}` : ''}`}>
        <div className="card-name">{p.name}</div><div className="card-district">{districtName(p.district_code, lang, p.district)}</div>
        <div className="card-price">{p.price_per_bag_per_hour} ₸ {t.perBagPerHour}</div>
      </Link>)}</div>}
  </main></div>;
}
