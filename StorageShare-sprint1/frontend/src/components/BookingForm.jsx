import { useState } from 'react';
import { createBooking } from '../api/bookings';
import { validateBooking } from '../lib/validate';
import { formErrors } from '../lib/errors';
import { useLang } from '../lib/lang-context';
import Field from './Field';
import Button from './Button';
import ErrorBanner from './ErrorBanner';
import PaymentPanel from './PaymentPanel';
import DateTimeField from './DateTimeField';

function estimateTotal(pricePerHour, bags, dropOffAt, pickUpAt) {
  const hours = (new Date(pickUpAt) - new Date(dropOffAt)) / 3600000;
  if (!(hours > 0) || !(bags > 0)) return null;
  return (Number(pricePerHour) * bags * hours).toFixed(2);
}

function capacityLeft(message) {
  const match = /(\d+)\s*bag/.exec(message || '');
  return match ? Number(match[1]) : null;
}

function minutesOf(value) {
  const [hours, minutes] = String(value).split(':').map(Number);
  return hours * 60 + minutes;
}

function timeSlots(opensAt, closesAt, step = 30) {
  const start = minutesOf(opensAt);
  const end = minutesOf(closesAt);
  const slots = [];
  for (let point = start; point <= end; point += step) {
    const hours = String(Math.floor(point / 60)).padStart(2, '0');
    const minutes = String(point % 60).padStart(2, '0');
    slots.push(`${hours}:${minutes}`);
  }
  return slots;
}

export default function BookingForm({ point }) {
  const { t } = useLang();
  const [dropOffDate, setDropOffDate] = useState('');
  const [dropOffTime, setDropOffTime] = useState('');
  const [pickUpDate, setPickUpDate] = useState('');
  const [pickUpTime, setPickUpTime] = useState('');
  const [bagsCount, setBagsCount] = useState('1');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(null);

  const today = new Date().toLocaleDateString('en-CA');
  const slots = timeSlots(point.opens_at, point.closes_at);
  const dropOffAt = dropOffDate && dropOffTime ? `${dropOffDate}T${dropOffTime}` : '';
  const pickUpAt = pickUpDate && pickUpTime ? `${pickUpDate}T${pickUpTime}` : '';

  function message(value) {
    if (!value) return undefined;
    if (typeof value === 'object') return `${t.notEnoughCapacity} ${value.capacity}`;
    return t[value] || value;
  }

  function chooseDropOffDate(value) {
    setDropOffDate(value);
    if (!pickUpDate) setPickUpDate(value);
  }

  function reset() {
    setBooking(null); setDropOffDate(''); setDropOffTime('');
    setPickUpDate(''); setPickUpTime(''); setBagsCount('1');
  }

  const estimate = estimateTotal(
    point.price_per_bag_per_hour, Number(bagsCount), dropOffAt, pickUpAt,
  );

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    const errs = validateBooking({
      dropOffAt, pickUpAt, bagsCount,
      opensAt: point.opens_at, closesAt: point.closes_at,
    });
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
    return <PaymentPanel booking={booking} point={point} onBookAnother={reset} />;
  }

  return <div className="booking-card">
    <h2 className="booking-title">{t.bookingTitle}</h2>
    <ErrorBanner message={message(banner)} />
    <form onSubmit={handleSubmit} noValidate>
      <div className="form-fields">
        <DateTimeField label={t.dropOff} date={dropOffDate} time={dropOffTime}
          onDate={chooseDropOffDate} onTime={setDropOffTime} min={today}
          slots={slots} error={message(errors.drop_off_at)}
          dateAria={`${t.dropOff} — ${t.dateLabel}`} timeAria={`${t.dropOff} — ${t.timeLabel}`} />
        <DateTimeField label={t.pickUp} date={pickUpDate} time={pickUpTime}
          onDate={setPickUpDate} onTime={setPickUpTime} min={dropOffDate || today}
          slots={slots} error={message(errors.pick_up_at)}
          dateAria={`${t.pickUp} — ${t.dateLabel}`} timeAria={`${t.pickUp} — ${t.timeLabel}`} />
        <Field label={t.bags} type="number" value={bagsCount} min="1"
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