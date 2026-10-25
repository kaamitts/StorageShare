import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStoragePointById } from '../api/storage';
import { useLang } from '../lib/LangContext';
import LangSwitcher from '../components/LangSwitcher';

export default function StorageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { lang, t } = useLang();
  const [point, setPoint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setLoading(true);
    getStoragePointById(id)
      .then(data => { setPoint(data); setLoading(false); })
      .catch(() => { setNotFound(true); setLoading(false); });
  }, [id]);

  return (
    <div className="search-page">
      <header className="search-header">
        <span className="search-logo">STORAGESHARE</span>
        <LangSwitcher />
      </header>

      <main className="search-main">
        <button className="back-btn" onClick={() => navigate('/search')}>
          {t.backToList}
        </button>

        {loading ? (
          <p className="search-empty">{t.loading}</p>
        ) : notFound ? (
          <p className="search-empty">{t.notFound}</p>
        ) : (
          <div className="detail-card">
            <h1 className="detail-name">{point.name}</h1>

            <div className="detail-rows">
              <div className="detail-row">
                <span className="detail-label">{t.district}</span>
                <span className="detail-value">{point.district[lang]}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">{t.area}</span>
                <span className="detail-value">{point.area_m2} {t.areaUnit}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">{t.price}</span>
                <span className="detail-value detail-price">{point.price_per_bag_per_day} ₸ {t.perBagPerDay}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">{t.hours}</span>
                <span className="detail-value">{point.open_hours}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">{t.contact}</span>
                <span className="detail-value">{point.phone}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">{t.address || 'Address'}</span>
                <span className="detail-value">{point.address[lang]}</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}