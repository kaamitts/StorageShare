import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getDistricts, getStoragePoints } from '../api/storage';
import { useLang } from '../lib/lang-context';
import { districtName } from '../lib/districts';
import Header from '../components/Header';
import Dropdown from '../components/Dropdown';
export default function SearchPage() {
  const { lang, t } = useLang();
  const [params, setParams] = useSearchParams(); const district = params.get('district') || '';
  const is24Hours = params.get('is_24_hours') === 'true';
  const openNow = params.get('open_now') === 'true';
  const hasFilters = Boolean(district || is24Hours || openNow);
  const [result, setResult] = useState({ districts: [], points: [], loading: true, error: false });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getDistricts(controller.signal),
      getStoragePoints(district, controller.signal, { is24Hours, openNow }),
    ])
      .then(([districts, points]) => setResult({ districts, points, loading: false, error: false }))
      .catch(error => { if (error.name !== 'AbortError') setResult(v => ({ ...v, loading: false, error: true })); });
    return () => controller.abort();
  }, [district, is24Hours, openNow, attempt]);
  useEffect(() => {
    if (!openNow) return undefined;
    const interval = window.setInterval(() => setAttempt(value => value + 1), 60_000);
    return () => window.clearInterval(interval);
  }, [openNow]);
  function updateParam(name, value) {
    setResult(v => ({ ...v, loading: true, error: false }));
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    setParams(next);
  }
  function choose(value) { updateParam('district', value); }
  function resetFilters() {
    setResult(v => ({ ...v, loading: true, error: false }));
    setParams({});
  }
  return <div className="search-page"><Header /><main className="search-main">
    <h1 className="search-title">{t.findStorage}</h1>
    <Dropdown ariaLabel={t.district} value={district} onChange={choose}
      placeholder={t.allDistricts}
      options={[{ value: '', label: t.allDistricts },
        ...result.districts.map(d => ({ value: d.code, label: districtName(d.code, lang, d.name) }))]} />
    <div className="storage-filters" role="group" aria-label={t.storageFilters}>
      <label className="storage-filter">
        <input type="checkbox" checked={is24Hours}
          onChange={event => updateParam('is_24_hours', event.target.checked ? 'true' : '')} />
        <span>{t.filter24Hours}</span>
      </label>
      <label className="storage-filter">
        <input type="checkbox" checked={openNow}
          onChange={event => updateParam('open_now', event.target.checked ? 'true' : '')} />
        <span>{t.filterOpenNow}</span>
      </label>
      {hasFilters && <button className="storage-filter-reset" type="button" onClick={resetFilters}>
        {t.clearFilters}
      </button>}
    </div>
    {result.loading ? <p>{t.loading}</p> : result.error ? <div role="alert">{t.requestError} <button onClick={() => { setResult(v => ({ ...v, loading: true })); setAttempt(a => a + 1); }}>{t.retry}</button></div> : result.points.length === 0 ? <p className="search-empty">{hasFilters ? t.noMatchingPoints : t.noPoints}</p> :
      <div className="cards-grid">{result.points.map(p => <Link className="card" key={p.id} to={`/storage/${p.id}${params.toString() ? `?${params}` : ''}`}>
        <div className="card-name">{p.name}</div><div className="card-district">{districtName(p.district_code, lang, p.district)}</div>
        <div className="card-price">{p.price_per_bag_per_hour} ₸ {t.perBagPerHour}</div>
      </Link>)}</div>}
  </main></div>;
}
