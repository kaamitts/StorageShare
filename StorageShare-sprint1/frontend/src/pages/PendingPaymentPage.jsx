import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { cancelPendingBooking, getPendingBooking } from '../api/bookings';
import Header from '../components/Header';
import { useLang } from '../lib/lang-context';
import { formatMoment } from '../lib/datetime';

function loadPendingBooking(signal) {
  return getPendingBooking(signal).then(booking => ({
    booking,
    deadline: booking
      ? Date.now() + booking.payment_seconds_remaining * 1000
      : null,
  }));
}

function formatCountdown(seconds) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`;
}

export default function PendingPaymentPage() {
  const { lang, t } = useLang();
  const navigate = useNavigate();
  const [result, setResult] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);
  const [now, setNow] = useState(Date.now());
  const [expired, setExpired] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    loadPendingBooking(controller.signal)
      .then(data => setResult(data))
      .catch(error => {
        if (error.name !== 'AbortError') setResult({ error });
      });
    return () => controller.abort();
  }, [attempt]);

  useEffect(() => {
    if (result.deadline == null) return undefined;
    let refreshed = false;
    const interval = setInterval(() => {
      const currentTime = Date.now();
      setNow(currentTime);
      if (!refreshed && currentTime >= result.deadline) {
        refreshed = true;
        setExpired(true);
        setAttempt(value => value + 1);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [result.deadline]);

  const secondsRemaining = result.deadline == null
    ? 0
    : Math.max(0, Math.ceil((result.deadline - now) / 1000));

  function retry() {
    setResult({ loading: true });
    setAttempt(value => value + 1);
  }

  async function cancelBooking() {
    if (!booking || cancelling || !window.confirm(t.confirmCancelPending)) return;
    setCancelling(true);
    setCancelError('');
    try {
      const updated = await cancelPendingBooking(booking.id);
      if (updated.status === 'cancelled') setCancelled(true);
      else setExpired(true);
      setResult({ loading: true });
      setAttempt(value => value + 1);
    } catch (error) {
      setCancelError(error.status === 409 ? t.cancellationNotAllowed : t.requestError);
    } finally {
      setCancelling(false);
    }
  }

  const booking = result.booking;

  return <div className="search-page">
    <Header />
    <main className="search-main">
      <Link className="back-btn" to="/search">{t.backToList}</Link>
      <h1 className="search-title">{t.pendingPayment}</h1>
      {result.loading ? <p>{t.loading}</p>
        : result.error ? <div role="alert">{t.requestError}{' '}
            <button type="button" onClick={retry}>{t.retry}</button></div>
        : !booking ? <div className="pending-payment-empty">
            <p className={expired ? 'demo-payment-error' : 'search-empty'}>
              {cancelled ? t.pendingBookingCancelled
                : expired ? t.bookingExpired : t.pendingPaymentEmpty}
            </p>
            <Link className="btn-secondary" to="/search">{t.findStorage}</Link>
          </div>
        : <div className="history-list traveler-history-list">
            <article className="booking-card history-booking-card pending-booking-card">
              <div className="history-booking-main">
                <h2 className="booking-title">{booking.storage_point.name}</h2>
                <div className="detail-rows history-booking-details">
                  {[[t.bookingNumber, `#${booking.traveler_booking_number}`],
                    [t.address, booking.storage_point.address],
                    [t.dropOff, formatMoment(booking.drop_off_at, lang)],
                    [t.pickUp, formatMoment(booking.pick_up_at, lang)],
                    [t.bags, booking.bags_count],
                    [t.total, `${booking.total_price} ₸`],
                    [t.statusLabel, t.awaitingPayment]]
                    .map(([label, value]) =>
                      <div className="detail-row" key={label}>
                        <span className="detail-label">{label}</span>
                        <span className="detail-value">{value}</span>
                      </div>)}
                </div>
              </div>
              <aside className="pending-booking-action">
                <button type="button" className="btn-primary"
                  disabled={secondsRemaining === 0}
                  onClick={() => navigate('/demo-payment', { state: { bookingId: booking.id } })}>
                  {t.payBtn}
                </button>
                <p className={secondsRemaining === 0 ? 'booking-hint expired-time' : 'booking-hint'}>
                  {t.paymentTimeLeft}: <strong>{formatCountdown(secondsRemaining)}</strong>
                </p>
                <button type="button" className="pending-cancel-button"
                  disabled={cancelling} onClick={cancelBooking}>
                  {cancelling ? t.cancellingBooking : t.cancelBooking}
                </button>
                {cancelError && <p className="pending-cancel-error" role="alert">{cancelError}</p>}
              </aside>
            </article>
          </div>}
    </main>
  </div>;
}
