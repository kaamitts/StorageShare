import { useState } from 'react';
import { payBooking } from '../api/bookings';
import { useLang } from '../lib/lang-context';
import Button from './Button';
import ErrorBanner from './ErrorBanner';

const LOCALES = { kk: 'kk-KZ', ru: 'ru-RU', en: 'en-GB' };

function formatMoment(value, lang) {
  return new Date(value).toLocaleString(LOCALES[lang] || 'en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export default function PaymentPanel({ booking, point, onBookAnother }) {
  const { lang, t } = useLang();
  const [current, setCurrent] = useState(booking);
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);

  const paid = current.status !== 'awaiting_payment';

  async function handlePay(e) {
    e.preventDefault();
    if (loading || paid) return;
    setBanner(''); setLoading(true);
    try {
      setCurrent(await payBooking(current.id));
    } catch (err) {
      if (err.status === 409) setBanner('bookingConflict');
      else if (err.status === 404) setBanner('bookingNotFound');
      else setBanner('requestError');
    } finally { setLoading(false); }
  }

  return <div className="booking-card">
    <h2 className="booking-title">{paid ? t.paymentDone : t.paymentTitle}</h2>
    <ErrorBanner message={banner ? t[banner] : ''} />
    <div className="detail-rows">
      {[[t.bookingNumber, `#${current.id}`],
        [t.storagePoint, point.name],
        [t.dropOff, formatMoment(current.drop_off_at, lang)],
        [t.pickUp, formatMoment(current.pick_up_at, lang)],
        [t.bags, current.bags_count],
        [t.total, `${current.total_price} ₸`],
        [t.statusLabel, paid ? t.confirmed : t.awaitingPayment]].map(([label, value]) =>
        <div className="detail-row" key={label}>
          <span className="detail-label">{label}</span>
          <span className="detail-value">{value}</span>
        </div>)}
    </div>
    {paid
      ? <>
          <p className="booking-hint">{t.paymentDoneHint}</p>
          <button className="btn-secondary" type="button" onClick={onBookAnother}>
            {t.bookAnother}
          </button>
        </>
      : <>
          <p className="booking-demo">{t.demoNotice}</p>
          <form onSubmit={handlePay}><Button loading={loading}>{t.payBtn}</Button></form>
        </>}
  </div>;
}