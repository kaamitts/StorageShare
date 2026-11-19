import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { deleteMyStoragePoint, getMyStoragePoints } from '../api/storage';
import Header from '../components/Header';
import { districtName } from '../lib/districts';
import { useLang } from '../lib/lang-context';

export default function MyStoragePointsPage() {
  const { lang, t } = useLang();
  const [result, setResult] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    getMyStoragePoints(controller.signal)
      .then(points => setResult({ points }))
      .catch(error => {
        if (error.name !== 'AbortError') setResult({ error });
      });
    return () => controller.abort();
  }, [attempt]);

  function retry() {
    setResult({ loading: true });
    setAttempt(value => value + 1);
  }

  async function removePoint(point) {
    if (!window.confirm(t.confirmDeletePoint)) return;
    setDeletingId(point.id);
    setDeleteError('');
    try {
      await deleteMyStoragePoint(point.id);
      setResult(current => ({
        points: current.points.filter(item => item.id !== point.id),
      }));
    } catch (error) {
      setDeleteError(error.status === 409 ? t.pointHasBookings : t.requestError);
    } finally {
      setDeletingId(null);
    }
  }

  return <div className="search-page">
    <Header />
    <main className="search-main">
      <Link className="back-btn" to="/partner">{t.backToPartner}</Link>
      <div className="my-points-heading">
        <h1 className="search-title">{t.myStoragePoints}</h1>
        <Link className="btn-primary my-points-add" to="/partner">{t.addPoint}</Link>
      </div>
      {deleteError && <p className="point-delete-error" role="alert">{deleteError}</p>}

      {result.loading ? <p>{t.loading}</p>
        : result.error ? <div className="my-points-error" role="alert">
          <p>{t.requestError}</p>
          <button className="btn-secondary my-points-retry" onClick={retry}>{t.retry}</button>
        </div>
        : result.points.length === 0 ? <div className="my-points-empty">
          <p className="search-empty">{t.noMyStoragePoints}</p>
          <Link className="btn-secondary my-points-empty-add" to="/partner">{t.addPoint}</Link>
        </div>
        : <div className="partner-points-grid">
          {result.points.map(point => <article className="partner-point-card" key={point.id}>
            <div className="partner-point-card-heading">
              <h2 className="booking-title">{point.name}</h2>
              <span className={`point-status${point.is_active ? ' active' : ' inactive'}`}>
                {point.is_active ? t.pointActive : t.pointInactive}
              </span>
            </div>
            <dl className="partner-point-details">
              <div><dt>{t.address}</dt><dd>{point.address}</dd></div>
              <div><dt>{t.district}</dt><dd>{districtName(point.district_code, lang, point.district)}</dd></div>
              <div><dt>{t.workingHours}</dt><dd>
                {point.is_24_hours || point.opens_at === point.closes_at
                  ? t.open24Hours : `${point.opens_at} – ${point.closes_at}`}
              </dd></div>
            </dl>
            <div className="partner-point-actions">
              <button type="button" className="point-delete-button"
                disabled={deletingId !== null} aria-busy={deletingId === point.id}
                onClick={() => removePoint(point)}>
                {deletingId === point.id ? t.deletingPoint : t.deletePoint}
              </button>
            </div>
          </article>)}
        </div>}
    </main>
  </div>;
}
