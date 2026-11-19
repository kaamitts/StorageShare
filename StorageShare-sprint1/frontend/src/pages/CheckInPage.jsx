import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getBookingByToken, checkInBooking, checkOutBooking } from '../api/bookings';
import { useLang } from '../lib/lang-context';
import { formatMoment } from '../lib/datetime';
import Header from '../components/Header';
import Button from '../components/Button';
import ErrorBanner from '../components/ErrorBanner';

const STATUS_KEYS = {
  awaiting_payment: 'awaitingPayment',
  expired: 'expired',
  confirmed: 'confirmed',
  checked_in: 'checkedIn',
  completed: 'completed',
  cancelled: 'cancelled',
};

const NO_ACTION_KEYS = {
  awaiting_payment: 'bookingNotPaid',
  expired: 'bookingExpired',
  completed: 'bookingCompleted',
  cancelled: 'bookingCancelledMsg',
};

function Shell({ children }) {
  return <div className="search-page"><Header /><main className="search-main">{children}</main></div>;
}

export default function CheckInPage() {
  const { token } = useParams();
  const { lang, t } = useLang();
  const [result, setResult] = useState({ loading: true });
  const [banner, setBanner] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getBookingByToken(token, controller.signal)
      .then(booking => setResult({ booking }))
      .catch(error => { if (error.name !== 'AbortError') setResult({ error }); });
    return () => controller.abort();
  }, [token, attempt]);

  async function run(action) {
    if (busy) return;
    setBanner(''); setBusy(true);
    try {
      setResult({ booking: await action(token) });
    } catch (err) {
      if (err.status === 409) { setBanner('statusChanged'); setAttempt(a => a + 1); }
      else if (err.status === 403) setBanner('otherPartner');
      else if (err.status === 404) setBanner('qrNotFound');
      else setBanner('requestError');
    } finally { setBusy(false); }
  }

  if (result.loading) return <Shell><p>{t.loading}</p></Shell>;

  if (result.error) {
    const known = result.error.status === 404 || result.error.status === 403;
    const key = result.error.status === 404 ? 'qrNotFound'
      : result.error.status === 403 ? 'otherPartner' : 'requestError';
    return <Shell>
      <div className="booking-card">
        <h2 className="booking-title">{t.checkInTitle}</h2>
        <ErrorBanner message={t[key]} />
        {!known && <button className="btn-secondary" type="button"
          onClick={() => { setResult({ loading: true }); setAttempt(a => a + 1); }}>{t.retry}</button>}
      </div>
    </Shell>;
  }

  const booking = result.booking;
  const noActionKey = NO_ACTION_KEYS[booking.status];

  return <Shell>
    <div className="booking-card">
      <h2 className="booking-title">{booking.storage_point.name}</h2>
      <ErrorBanner message={banner ? t[banner] : ''} />
      <div className="detail-rows">
        {[[t.bookingNumber, `#${booking.id}`],
          [t.address, booking.storage_point.address],
          [t.traveler, booking.traveler_name],
          [t.dropOff, formatMoment(booking.drop_off_at, lang)],
          [t.pickUp, formatMoment(booking.pick_up_at, lang)],
          [t.bags, booking.bags_count],
          [t.total, `${booking.total_price} ₸`],
          [t.statusLabel, t[STATUS_KEYS[booking.status]] || booking.status],
          ...(booking.checked_in_at
            ? [[t.checkedInAt, formatMoment(booking.checked_in_at, lang)]] : []),
          ...(booking.checked_out_at
            ? [[t.checkedOutAt, formatMoment(booking.checked_out_at, lang)]] : [])]
          .map(([label, value]) =>
            <div className="detail-row" key={label}>
              <span className="detail-label">{label}</span>
              <span className="detail-value">{value}</span>
            </div>)}
      </div>
      {booking.can_check_in &&
        <form onSubmit={e => { e.preventDefault(); run(checkInBooking); }}>
          <Button loading={busy}>{t.checkIn}</Button>
        </form>}
      {booking.can_check_out &&
        <form onSubmit={e => { e.preventDefault(); run(checkOutBooking); }}>
          <Button loading={busy}>{t.checkOut}</Button>
        </form>}
      {!booking.can_check_in && !booking.can_check_out && noActionKey &&
        <p className="booking-hint">{t[noActionKey]}</p>}
    </div>
  </Shell>;
}
