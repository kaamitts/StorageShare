import { useState, useEffect } from 'react';
import { getDistricts, getStoragePoints } from '../api/storage';
import { useLang } from '../lib/LangContext';
import LangSwitcher from '../components/LangSwitcher';

export default function SearchPage() {
  const { lang, t } = useLang();
  const [districts, setDistricts] = useState([]);
  const [districtIndex, setDistrictIndex] = useState('');
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getDistricts(lang).then(setDistricts);
    setDistrictIndex('');
  }, [lang]);

  useEffect(() => {
    setLoading(true);
    getStoragePoints(districtIndex === '' ? '' : Number(districtIndex), lang).then(data => {
      setPoints(data);
      setLoading(false);
    });
  }, [districtIndex, lang]);

  return (
    <div className="search-page">
      <header className="search-header">
        <span className="search-logo">STORAGESHARE</span>
        <LangSwitcher />
      </header>
      <main className="search-main">
        <h1 className="search-title">{t.findStorage}</h1>
        <select
          className="district-select"
          value={districtIndex}
          onChange={e => setDistrictIndex(e.target.value)}
        >
          <option value="">{t.allDistricts}</option>
          {districts.map((d, i) => (
            <option key={i} value={i}>{d}</option>
          ))}
        </select>

        {loading ? (
          <p className="search-empty">{t.loading}</p>
        ) : points.length === 0 ? (
          <p className="search-empty">{t.noPoints}</p>
        ) : (
          <div className="cards-grid">
            {points.map(p => (
              <div key={p.id} className="card">
                <div className="card-name">{p.name}</div>
                <div className="card-district">{p.district[lang]}</div>
                <div className="card-price">{p.price_per_bag_per_day} ₸ {t.perBagPerDay}</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}