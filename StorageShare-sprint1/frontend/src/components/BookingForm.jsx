import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createBooking, getPendingBooking } from '../api/bookings';
import { validateBooking } from '../lib/validate';
import { formErrors } from '../lib/errors';
import { useLang } from '../lib/lang-context';
import Field from './Field';
import Button from './Button';
import ErrorBanner from './ErrorBanner';
import DateTimeField from './DateTimeField';
import { createTimeSlots } from '../lib/time-slots';
import { dateInTimeZone, zonedDateTimeToISOString } from '../lib/zoned-time';

function estimateTotal(pricePerHour, bags, dropOffAt, pickUpAt) {
  const dropDate = dropOffAt.slice(0, 10);
  const dropTime = dropOffAt.slice(11, 16);
  const pickDate = pickUpAt.slice(0, 10);
  const pickTime = pickUpAt.slice(11, 16);
  const dropInstant = zonedDateTimeToISOString(dropDate, dropTime);
  const pickInstant = zonedDateTimeToISOString(pickDate, pickTime);
  if (!dropInstant || !pickInstant) return null;
  const hours = (new Date(pickInstant) - new Date(dropInstant)) / 3600000;
  if (!(hours > 0) || !(bags > 0)) return null;
  return (Number(pricePerHour) * bags * hours).toFixed(2);
}

function capacityLeft(message) {
  const match = /(\d+)\s*bag/.exec(message || '');
  return match ? Number(match[1]) : null;
}

export default function BookingForm({ point }) {
  const { t } = useLang();
  const navigate = useNavigate();
  const [dropOffDate, setDropOffDate] = useState('');
  const [dropOffTime, setDropOffTime] = useState('');
  const [pickUpDate, setPickUpDate] = useState('');
  const [pickUpTime, setPickUpTime] = useState('');
  const [bagsCount, setBagsCount] = useState('1');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingBooking, setPendingBooking] = useState(null);
  const [checkingPending, setCheckingPending] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    getPendingBooking(controller.signal)
      .then(setPendingBooking)
      .catch(error => { if (error.name !== 'AbortError') setPendingBooking(null); })
      .finally(() => { if (!controller.signal.aborted) setCheckingPending(false); });
    return () => controller.abort();
  }, []);

  const today = dateInTimeZone();
  const slots = createTimeSlots(point.opens_at, point.closes_at, {
    is24Hours: point.is_24_hours,
  });
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

  const estimate = estimateTotal(
    point.price_per_bag_per_hour, Number(bagsCount), dropOffAt, pickUpAt,
  );

  async function submitBooking(payNow) {
    if (loading || checkingPending || pendingBooking) return;
    const errs = validateBooking({
      dropOffAt, pickUpAt, bagsCount,
      opensAt: point.opens_at, closesAt: point.closes_at,
      is24Hours: point.is_24_hours,
    });
    if (Object.keys(errs).length) { setErrors(errs); setBanner('checkFields'); return; }
    setErrors({}); setBanner(''); setLoading(true);
    try {
      const created = await createBooking({
        storagePointId: point.id,
        dropOffAt: zonedDateTimeToISOString(dropOffDate, dropOffTime),
        pickUpAt: zonedDateTimeToISOString(pickUpDate, pickUpTime),
        bagsCount: Number(bagsCount),
      });
      if (payNow) navigate('/demo-payment', { state: { bookingId: created.id } });
      else navigate('/pending-payment');
    } catch (err) {
      if (err.status === 409) {
        getPendingBooking()
          .then(booking => {
            setPendingBooking(booking);
            if (!booking) setBanner('pendingBookingExists');
          })
          .catch(() => setBanner('pendingBookingExists'));
        return;
      }
      const fields = formErrors(err);
      const left = capacityLeft(fields.bags_count);
      if (left !== null) fields.bags_count = { capacity: left };
      setErrors(fields);
      if (err.status === 400) setBanner('checkFields');
      else if (err.status === 403) setBanner('travellersOnly');
      else setBanner('requestError');
    } finally { setLoading(false); }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    await submitBooking(false);
  }

  return <div className="booking-card compact-booking-card">
    <h2 className="booking-title">{t.bookingTitle}</h2>
    <ErrorBanner message={message(banner)} />
    {pendingBooking && <div className="booking-demo pending-booking-notice">
      {t.pendingBookingExists}{' '}
      <Link to="/pending-payment">{t.pendingPayment}</Link>
    </div>}
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
      <div className="booking-actions">
        <Button loading={loading} disabled={checkingPending || Boolean(pendingBooking)}>{t.bookBtn}</Button>
        <button type="button" className="btn-primary" disabled={loading || checkingPending || Boolean(pendingBooking)}
          onClick={() => submitBooking(true)}>{t.payNowBtn}</button>
      </div>
      {!pendingBooking && <p className="payment-reservation-note">{t.paymentReservationNotice}</p>}
    </form>
  </div>;
}
