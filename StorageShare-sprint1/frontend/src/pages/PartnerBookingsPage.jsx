import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPartnerBookings } from '../api/bookings';
import { useLang } from '../lib/lang-context';
import { formatMoment } from '../lib/datetime';
import Header from '../components/Header';

const STATUS_KEYS = {
  awaiting_payment: 'awaitingPayment',
  expired: 'expired',
  confirmed: 'confirmed',
  checked_in: 'checkedIn',
  completed: 'completed',
  cancelled: 'cancelled',
};

export default function PartnerBookingsPage() {
  const { lang, t } = useLang();
  const [result, setResult] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getPartnerBookings(controller.signal)
      .then(bookings => setResult({ bookings }))
      .catch(error => { if (error.name !== 'AbortError') setResult({ error }); });
    return () => controller.abort();
  }, [attempt]);

  function retry() { setResult({ loading: true }); setAttempt(a => a + 1); }

  return <div className="search-page"><Header /><main className="search-main">
    <Link className="back-btn" to="/partner">{t.backToPartner}</Link>
    <h1 className="search-title">{t.partnerBookings}</h1>
    {result.loading ? <p>{t.loading}</p>
      : result.error ? <div role="alert">{t.requestError}
          <button onClick={retry}>{t.retry}</button></div>
      : result.bookings.length === 0 ? <p className="search-empty">{t.noPartnerBookings}</p>
      : <div className="history-list">
          {result.bookings.map(booking => <article className="booking-card partner-booking-card" key={booking.id}>
            <h2 className="booking-title">{booking.storage_point_name}</h2>
            <div className="detail-rows">
              {[[t.bookingNumber, `#${booking.id}`],
                [t.dropOff, formatMoment(booking.drop_off_at, lang)],
                [t.pickUp, formatMoment(booking.pick_up_at, lang)],
                [t.bags, booking.bags_count],
                [t.statusLabel, t[STATUS_KEYS[booking.status]] || booking.status],
                // Only filled in once the partner has actually scanned the QR.
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
          </article>)}
        </div>}
  </main></div>;
}
