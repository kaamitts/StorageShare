import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDistricts, createStoragePoint } from '../api/storage';
import { validateStoragePoint } from '../lib/validate';
import { formErrors } from '../lib/errors';
import { useLang } from '../lib/lang-context';
import { districtName } from '../lib/districts';
import Field from './Field';
import Button from './Button';
import ErrorBanner from './ErrorBanner';
import Dropdown from './Dropdown';

const EMPTY = {
  name: '', address: '', district: '', price_per_bag_per_hour: '',
  capacity_bags: '', opens_at: '', closes_at: '', security_notes: '',
};

export default function StoragePointForm() {
  const { lang, t } = useLang();
  const [form, setForm] = useState(EMPTY);
  const [districts, setDistricts] = useState([]);
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    getDistricts(controller.signal).then(setDistricts)
      .catch(error => { if (error.name !== 'AbortError') setBanner('requestError'); });
    return () => controller.abort();
  }, []);

  function set(key) { return value => setForm(current => ({ ...current, [key]: value })); }

  function message(value) { return value ? t[value] || value : undefined; }

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    const errs = validateStoragePoint(form);
    if (Object.keys(errs).length) { setErrors(errs); setBanner('checkFields'); setCreated(null); return; }
    setErrors({}); setBanner(''); setCreated(null); setLoading(true);
    try {
      const point = await createStoragePoint({
        ...form,
        capacity_bags: Number(form.capacity_bags),
        security_notes: form.security_notes.trim(),
      });
      setCreated(point);
      setForm(EMPTY);
    } catch (err) {
      setErrors(formErrors(err));
      if (err.status === 400) setBanner('checkFields');
      else if (err.status === 403) setBanner('partnersOnly');
      else setBanner('requestError');
    } finally { setLoading(false); }
  }

  return <div className="booking-card">
    <h2 className="booking-title">{t.addPoint}</h2>
    {created && <div className="banner-ok" role="status">
      {t.pointCreated}{' '}
      <Link to={`/search?district=${encodeURIComponent(created.district)}`}>{t.seeInSearch}</Link>
    </div>}
    <ErrorBanner message={message(banner)} />
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-fields">
        <Field label={t.pointName} value={form.name}
          onChange={set('name')} error={message(errors.name)} />
        <Field label={t.address} value={form.address}
          onChange={set('address')} error={message(errors.address)} />
        <div className="field">
          <label>{t.district}</label>
          <Dropdown wide ariaLabel={t.district} value={form.district}
            onChange={set('district')} placeholder={t.chooseDistrict}
            error={Boolean(errors.district)}
            options={districts.map(d => ({ value: d.code, label: districtName(d.code, lang, d.name) }))} />
          {errors.district && <span className="err-msg">{message(errors.district)}</span>}
        </div>
        <Field label={t.pricePerBagHour} type="number" value={form.price_per_bag_per_hour}
          onChange={set('price_per_bag_per_hour')} error={message(errors.price_per_bag_per_hour)} />
        <Field label={t.capacityBags} type="number" value={form.capacity_bags}
          onChange={set('capacity_bags')} error={message(errors.capacity_bags)} />
        <Field label={t.opensAt} type="time" value={form.opens_at}
          onChange={set('opens_at')} error={message(errors.opens_at)} />
        <Field label={t.closesAt} type="time" value={form.closes_at}
          onChange={set('closes_at')} error={message(errors.closes_at)} />
        <Field label={t.securityNotes} value={form.security_notes}
          onChange={set('security_notes')} error={message(errors.security_notes)} />
      </div>
      <Button loading={loading}>{t.savePoint}</Button>
    </form>
  </div>;
}