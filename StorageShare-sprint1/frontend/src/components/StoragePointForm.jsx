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
import TimePicker from './TimePicker';
import { createTimeSlots } from '../lib/time-slots';

const EMPTY = {
  name: '', address: '', district: '', price_per_bag_per_hour: '',
  capacity_bags: '', opens_at: '', closes_at: '', is_24_hours: false,
  security_notes: '',
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

  const timeOptions = createTimeSlots('00:00', '23:30');

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    const errs = validateStoragePoint(form);
    if (Object.keys(errs).length) { setErrors(errs); setBanner('checkFields'); setCreated(null); return; }
    setErrors({}); setBanner(''); setCreated(null); setLoading(true);
    try {
      const { opens_at, closes_at, ...pointData } = form;
      const point = await createStoragePoint({
        ...pointData,
        ...(form.is_24_hours ? {} : { opens_at, closes_at }),
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

  return <div className="booking-card storage-point-form-card">
    <h2 className="booking-title">{t.addPoint}</h2>
    {created && <div className="banner-ok" role="status">
      {t.pointCreated}{' '}
      <Link to={`/search?district=${encodeURIComponent(created.district)}`}>{t.seeInSearch}</Link>
    </div>}
    <ErrorBanner message={message(banner)} />
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-fields storage-point-form-fields">
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
        <label className={`hours-toggle${form.is_24_hours ? ' is-active' : ''}`}>
          <input type="checkbox" checked={form.is_24_hours}
            onChange={event => setForm(current => ({
              ...current,
              is_24_hours: event.target.checked,
            }))} />
          <span>{t.open24Hours}</span>
        </label>
        <div className={`field${form.is_24_hours ? ' field-disabled' : ''}`}>
          <label>{t.opensAt}</label>
          <TimePicker time={form.opens_at} onTime={set('opens_at')}
            slots={timeOptions} ariaLabel={t.opensAt} emptyLabel={t.chooseTime}
            hoursLabel={t.hoursLabel} minutesLabel={t.minutesLabel} quickPickLabel={t.quickPick}
            error={Boolean(errors.opens_at)} disabled={form.is_24_hours} />
          {errors.opens_at && <span className="err-msg">{message(errors.opens_at)}</span>}
        </div>
        <div className={`field${form.is_24_hours ? ' field-disabled' : ''}`}>
          <label>{t.closesAt}</label>
          <TimePicker time={form.closes_at} onTime={set('closes_at')}
            slots={timeOptions} ariaLabel={t.closesAt} emptyLabel={t.chooseTime}
            hoursLabel={t.hoursLabel} minutesLabel={t.minutesLabel} quickPickLabel={t.quickPick}
            error={Boolean(errors.closes_at)} disabled={form.is_24_hours} />
          {errors.closes_at && <span className="err-msg">{message(errors.closes_at)}</span>}
        </div>
        <Field label={t.securityNotes} value={form.security_notes}
          onChange={set('security_notes')} error={message(errors.security_notes)} />
      </div>
      <Button loading={loading}>{t.savePoint}</Button>
    </form>
  </div>;
}
