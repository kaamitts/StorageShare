import { lazy, Suspense, useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getDistricts, getStoragePoints } from '../api/storage';
import { useLang } from '../lib/lang-context';
import { districtName } from '../lib/districts';
import Header from '../components/Header';
import Dropdown from '../components/Dropdown';
const StorageMap = lazy(() => import('../components/StorageMap'));

function distanceKm(from, point) {
  if (point.latitude == null || point.longitude == null) return null;
  const radians = value => value * Math.PI / 180;
  const lat = Number(point.latitude);
  const lng = Number(point.longitude);
  const dLat = radians(lat - from[0]);
  const dLng = radians(lng - from[1]);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(radians(from[0])) * Math.cos(radians(lat)) * Math.sin(dLng / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export default function SearchPage() {
  const { lang, t } = useLang();
  const [params, setParams] = useSearchParams(); const district = params.get('district') || '';
  const is24Hours = params.get('is_24_hours') === 'true';
  const openNow = params.get('open_now') === 'true';
  const hasFilters = Boolean(district || is24Hours || openNow);
  const [result, setResult] = useState({ districts: [], points: [], loading: true, error: false });
  const [attempt, setAttempt] = useState(0);
  const [view, setView] = useState('list');
  const [focusPointId, setFocusPointId] = useState(null);
  const [userPosition, setUserPosition] = useState(null);
  const [locationError, setLocationError] = useState(false);
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
  function locateMe() {
    if (!navigator.geolocation) { setLocationError(true); return; }
    setLocationError(false);
    navigator.geolocation.getCurrentPosition(
      position => setUserPosition([position.coords.latitude, position.coords.longitude]),
      () => setLocationError(true),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }
  const orderedPoints = userPosition ? [...result.points].sort((a, b) => {
    const aDistance = distanceKm(userPosition, a) ?? Infinity;
    const bDistance = distanceKm(userPosition, b) ?? Infinity;
    return aDistance - bDistance;
  }) : result.points;
  const focusPoint = result.points.find(point => point.id === focusPointId);
  const focusPosition = focusPoint?.latitude != null && focusPoint?.longitude != null
    ? [Number(focusPoint.latitude), Number(focusPoint.longitude)] : null;
  const pointsWithLocations = result.points.filter(point => point.latitude != null && point.longitude != null);
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
    <div className="storage-view-controls">
      <div className="storage-view-toggle" role="group" aria-label={t.storageView}>
        <button type="button" className={view === 'list' ? 'active' : ''} onClick={() => setView('list')}>{t.listView}</button>
        <button type="button" className={view === 'map' ? 'active' : ''} onClick={() => setView('map')}>{t.mapView}</button>
      </div>
      {view === 'map' && <button type="button" className="locate-me-button" onClick={locateMe}>{t.locateMe}</button>}
    </div>
    {locationError && <p className="map-location-error" role="status">{t.locationUnavailable}</p>}
    {result.loading ? <p>{t.loading}</p> : result.error ? <div role="alert">{t.requestError} <button onClick={() => { setResult(v => ({ ...v, loading: true })); setAttempt(a => a + 1); }}>{t.retry}</button></div> : result.points.length === 0 ? <p className="search-empty">{hasFilters ? t.noMatchingPoints : t.noPoints}</p> :
      view === 'map' ? <div className="search-map-layout">
        <Suspense fallback={<p>{t.loading}</p>}><StorageMap points={pointsWithLocations.map(point => ({
          ...point,
          popupContent: <><strong>{point.name}</strong><br />
            {districtName(point.district_code, lang, point.district)}<br />
            {point.price_per_bag_per_hour} ₸ {t.perBagPerHour}<br />
            <Link to={`/storage/${point.id}${params.toString() ? `?${params}` : ''}`}>{t.viewPoint}</Link></>,
        }))} focusPosition={focusPosition} userPosition={userPosition} locationLabel={t.currentLocation} lang={lang} /></Suspense>
        {pointsWithLocations.length === 0 && <p className="map-empty-hint">{t.noPointsWithLocation}</p>}
      </div> : <div className="cards-grid">{orderedPoints.map(p => {
        const distance = userPosition && distanceKm(userPosition, p);
        return <article className="card" key={p.id}>
          <Link className="storage-card-link" to={`/storage/${p.id}${params.toString() ? `?${params}` : ''}`}>
            <div className="card-name">{p.name}</div><div className="card-district">{districtName(p.district_code, lang, p.district)}</div>
            <div className="card-price">{p.price_per_bag_per_hour} ₸ {t.perBagPerHour}</div>
            {distance != null && <div className="card-distance">{t.distanceAway.replace('{distance}', distance.toFixed(1))}</div>}
          </Link>
          {p.latitude != null && p.longitude != null && <button type="button" className="card-map-button"
            onClick={() => { setFocusPointId(p.id); setView('map'); }}>{t.showOnMap}</button>}
        </article>;
      })}</div>}
  </main></div>;
}
