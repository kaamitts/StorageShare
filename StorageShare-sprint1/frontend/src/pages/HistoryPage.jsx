import { useState, useEffect } from 'react';
import { getBookingHistory } from '../api/bookings';
import { useLang } from '../lib/lang-context';
import { formatMoment } from '../lib/datetime';
import Header from '../components/Header';

const STATUS_KEYS = {
  awaiting_payment: 'awaitingPayment',
  confirmed: 'confirmed',
  checked_in: 'checkedIn',
  completed: 'completed',
  cancelled: 'cancelled',
};

export default function HistoryPage() {
  const { lang, t } = useLang();
  const [result, setResult] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getBookingHistory(controller.signal)
      .then(bookings => setResult({ bookings }))
      .catch(error => { if (error.name !== 'AbortError') setResult({ error }); });
    return () => controller.abort();
  }, [attempt]);

  function retry() { setResult({ loading: true }); setAttempt(a => a + 1); }

  return <div className="search-page"><Header /><main className="search-main">
    <h1 className="search-title">{t.history}</h1>
    {result.loading ? <p>{t.loading}</p>
      : result.error ? <div role="alert">{t.requestError}
          <button onClick={retry}>{t.retry}</button></div>
      : result.bookings.length === 0 ? <p className="search-empty">{t.historyEmpty}</p>
      : <div className="history-list">
          {result.bookings.map(booking => <article className="booking-card" key={booking.id}>
            <h2 className="booking-title">{booking.storage_point.name}</h2>
            <div className="detail-rows">
              {[[t.bookingNumber, `#${booking.id}`],
                [t.address, booking.storage_point.address],
                [t.dropOff, formatMoment(booking.drop_off_at, lang)],
                [t.pickUp, formatMoment(booking.pick_up_at, lang)],
                [t.bags, booking.bags_count],
                [t.total, `${booking.total_price} ₸`],
                [t.statusLabel, t[STATUS_KEYS[booking.status]] || booking.status]]
                .map(([label, value]) =>
                  <div className="detail-row" key={label}>
                    <span className="detail-label">{label}</span>
                    <span className="detail-value">{value}</span>
                  </div>)}
            </div>
            {}
            {booking.qr && <div className="qr-block">
              <img className="qr-image" src={booking.qr.image} alt={t.qrAlt} />
              <p className="booking-hint">{t.qrHint}</p>
            </div>}
          </article>)}
        </div>}
  </main></div>;
}