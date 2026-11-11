import { useState } from 'react';
import { createBooking } from '../api/bookings';
import { validateBooking } from '../lib/validate';
import { formErrors } from '../lib/errors';
import { useLang } from '../lib/lang-context';
import Field from './Field';
import Button from './Button';
import ErrorBanner from './ErrorBanner';

function estimateTotal(pricePerHour, bags, dropOffAt, pickUpAt) {
  const hours = (new Date(pickUpAt) - new Date(dropOffAt)) / 3600000;
  if (!(hours > 0) || !(bags > 0)) return null;
  return (Number(pricePerHour) * bags * hours).toFixed(2);
}

function capacityLeft(message) {
  const match = /(\d+)\s*bag/.exec(message || '');
  return match ? Number(match[1]) : null;
}

export default function BookingForm({ point }) {
  const { t } = useLang();
  const [dropOffAt, setDropOffAt] = useState('');
  const [pickUpAt, setPickUpAt] = useState('');
  const [bagsCount, setBagsCount] = useState('1');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(null);

  function message(value) {
    if (!value) return undefined;
    if (typeof value === 'object') return `${t.notEnoughCapacity} ${value.capacity}`;
    return t[value] || value;
  }

  const estimate = estimateTotal(
    point.price_per_bag_per_hour, Number(bagsCount), dropOffAt, pickUpAt,
  );

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return; 
    const errs = validateBooking({ dropOffAt, pickUpAt, bagsCount });
    if (Object.keys(errs).length) { setErrors(errs); setBanner('checkFields'); return; }
    setErrors({}); setBanner(''); setLoading(true);
    try {
      const created = await createBooking({
        storagePointId: point.id,
        dropOffAt: new Date(dropOffAt).toISOString(),
        pickUpAt: new Date(pickUpAt).toISOString(),
        bagsCount: Number(bagsCount),
      });
      setBooking(created);
    } catch (err) {
      const fields = formErrors(err);
      const left = capacityLeft(fields.bags_count);
      if (left !== null) fields.bags_count = { capacity: left };
      setErrors(fields);
      if (err.status === 400) setBanner('checkFields');
      else if (err.status === 403) setBanner('travellersOnly');
      else setBanner('requestError');
    } finally { setLoading(false); }
  }

  if (booking) {
    return <div className="booking-card">
      <h2 className="booking-title">{t.bookingCreated}</h2>
      <div className="detail-rows">
        {[[t.bookingNumber, `#${booking.id}`],
          [t.bags, booking.bags_count],
          [t.total, `${booking.total_price} ₸`],
          [t.statusLabel, t.awaitingPayment]].map(([label, value]) =>
          <div className="detail-row" key={label}>
            <span className="detail-label">{label}</span>
            <span className="detail-value">{value}</span>
          </div>)}
      </div>
      <p className="booking-hint">{t.payNextStep}</p>
      <button className="btn-secondary" type="button" onClick={() => {
        setBooking(null); setDropOffAt(''); setPickUpAt(''); setBagsCount('1');
      }}>{t.bookAnother}</button>
    </div>;
  }

  return <div className="booking-card">
    <h2 className="booking-title">{t.bookingTitle}</h2>
    <ErrorBanner message={message(banner)} />
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-fields">
        <Field label={t.dropOff} type="datetime-local" value={dropOffAt}
          onChange={setDropOffAt} error={message(errors.drop_off_at)} />
        <Field label={t.pickUp} type="datetime-local" value={pickUpAt}
          onChange={setPickUpAt} error={message(errors.pick_up_at)} />
        <Field label={t.bags} type="number" value={bagsCount}
          onChange={setBagsCount} error={message(errors.bags_count)} />
      </div>
      {estimate && <div className="booking-total">
        <span className="detail-label">{t.estimatedTotal}</span>
        <span className="booking-total-value">{estimate} ₸</span>
      </div>}
      <Button loading={loading}>{t.bookBtn}</Button>
    </form>
  </div>;
}