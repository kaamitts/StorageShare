import { useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { payBooking } from '../api/bookings';
import Header from '../components/Header';
import { useLang } from '../lib/lang-context';

function formatCardNumber(digits) {
  return digits.match(/.{1,4}/g)?.join(' ') || '';
}

function formatExpiry(digits) {
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits;
}

function validatePaymentFields({ cardDigits, cardholder, expiryDigits, cvv }) {
  const errors = {};

  if (!cardDigits) errors.cardNumber = 'cardNumberRequired';
  else if (cardDigits.length !== 16) errors.cardNumber = 'cardNumberInvalid';

  const owner = cardholder.trim();
  if (!owner) errors.cardholder = 'cardholderRequired';
  else if (owner.length > 50 || !/^(?=.*[A-Za-z])[A-Za-z '-]{1,50}$/.test(owner)) {
    errors.cardholder = 'cardholderInvalid';
  }

  if (!expiryDigits) errors.expiry = 'cardExpiryRequired';
  else {
    const month = Number(expiryDigits.slice(0, 2));
    if (expiryDigits.length >= 2 && (month < 1 || month > 12)) {
      errors.expiry = 'cardExpiryMonth';
    } else if (expiryDigits.length !== 4) {
      errors.expiry = 'cardExpiryFormat';
    } else {
      const year = 2000 + Number(expiryDigits.slice(2));
      const now = new Date();
      if (year < now.getFullYear()
          || (year === now.getFullYear() && month < now.getMonth() + 1)) {
        errors.expiry = 'cardExpired';
      }
    }
  }

  if (!cvv) errors.cvv = 'cardCvvRequired';
  else if (cvv.length !== 3) errors.cvv = 'cardCvvInvalid';

  return errors;
}

export default function DemoPaymentPage() {
  const { t } = useLang();
  const { state } = useLocation();
  const navigate = useNavigate();
  const bookingId = state?.bookingId;
  const payingRef = useRef(false);
  const [brand, setBrand] = useState('visa');
  const [cardDigits, setCardDigits] = useState('');
  const [cardholder, setCardholder] = useState('');
  const [expiryDigits, setExpiryDigits] = useState('');
  const [cvv, setCvv] = useState('');
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState('');
  const [attempted, setAttempted] = useState(false);
  const [touched, setTouched] = useState({});

  const fieldErrors = validatePaymentFields({ cardDigits, cardholder, expiryDigits, cvv });
  const ready = Object.keys(fieldErrors).length === 0;
  const fieldError = name => (attempted || touched[name]) ? t[fieldErrors[name]] : '';
  const markTouched = name => setTouched(current => ({ ...current, [name]: true }));

  async function handleSubmit(event) {
    event.preventDefault();
    setAttempted(true);
    const errors = validatePaymentFields({ cardDigits, cardholder, expiryDigits, cvv });
    if (!bookingId || Object.keys(errors).length || payingRef.current) return;

    payingRef.current = true;
    setPaying(true);
    setError('');
    try {
      // Only the booking id is sent. Card inputs remain local to this page.
      await payBooking(bookingId);
      setCardDigits('');
      setCardholder('');
      setExpiryDigits('');
      setCvv('');
      navigate('/history', { replace: true });
    } catch (paymentError) {
      if (paymentError.data?.code === 'booking_payment_expired') setError(t.bookingExpired);
      else if (paymentError.status === 409) setError(t.bookingConflict);
      else if (paymentError.status === 404) setError(t.bookingNotFound);
      else setError(t.requestError);
    } finally {
      payingRef.current = false;
      setPaying(false);
    }
  }

  return <div className="search-page">
    <Header />
    <main className="search-main demo-payment-main">
      <section className="demo-payment-card">
        <div className="demo-payment-heading">
          <h1 className="search-title">{t.demoPaymentTitle}</h1>
          <p>{t.demoPaymentSubtitle}</p>
        </div>

        {!bookingId
          ? <>
              <div className="demo-payment-notice" role="alert">{t.paymentBookingRequired}</div>
              <Link className="btn-secondary" to="/history">{t.goToHistory}</Link>
            </>
          : <>
              <div className="demo-payment-notice" role="note">{t.demoPaymentDataNotice}</div>
              {error && <div className="demo-payment-error" role="alert">{error}</div>}

        <form className="demo-payment-form" onSubmit={handleSubmit} noValidate autoComplete="off">
          <fieldset className="demo-payment-brands">
            <legend>{t.paymentSystem}</legend>
            <label className={`demo-payment-brand${brand === 'visa' ? ' selected' : ''}`}>
              <input type="radio" name="demo-payment-brand" value="visa"
                checked={brand === 'visa'} onChange={() => setBrand('visa')} />
              <span>{t.visa}</span>
            </label>
            <label className={`demo-payment-brand${brand === 'mastercard' ? ' selected' : ''}`}>
              <input type="radio" name="demo-payment-brand" value="mastercard"
                checked={brand === 'mastercard'} onChange={() => setBrand('mastercard')} />
              <span>{t.mastercard}</span>
            </label>
          </fieldset>

          <label className="demo-payment-field">
            <span className="demo-payment-label">{t.cardNumber}</span>
            <input id="demo-card-number" type="text" inputMode="numeric" autoComplete="off"
              aria-invalid={Boolean(fieldError('cardNumber'))}
              aria-describedby={fieldError('cardNumber') ? 'demo-card-number-error' : undefined}
              placeholder={brand === 'visa' ? '4242 4242 4242 4242' : '5555 5555 5555 4444'}
              value={formatCardNumber(cardDigits)}
              onBlur={() => markTouched('cardNumber')}
              onChange={event => setCardDigits(event.target.value.replace(/\D/g, '').slice(0, 16))} />
            {fieldError('cardNumber') && <span id="demo-card-number-error" className="demo-payment-field-error">
              {fieldError('cardNumber')}
            </span>}
          </label>

          <label className="demo-payment-field">
            <span className="demo-payment-label">{t.cardholderName}</span>
            <input id="demo-cardholder" type="text" autoComplete="off"
              aria-invalid={Boolean(fieldError('cardholder'))}
              aria-describedby={fieldError('cardholder') ? 'demo-cardholder-error' : undefined}
              placeholder={t.cardholderPlaceholder} value={cardholder}
              onBlur={() => markTouched('cardholder')}
              onChange={event => setCardholder(event.target.value.replace(/[^A-Za-z '-]/g, '').slice(0, 50))} />
            {fieldError('cardholder') && <span id="demo-cardholder-error" className="demo-payment-field-error">
              {fieldError('cardholder')}
            </span>}
          </label>

          <div className="demo-payment-row">
            <label className="demo-payment-field">
              <span className="demo-payment-label">{t.cardExpiry}</span>
              <input id="demo-card-expiry" type="text" inputMode="numeric" autoComplete="off"
                placeholder="MM/YY" value={formatExpiry(expiryDigits)}
                aria-invalid={Boolean(fieldError('expiry'))}
                aria-describedby={fieldError('expiry') ? 'demo-card-expiry-error' : undefined}
                onBlur={() => markTouched('expiry')}
                onChange={event => setExpiryDigits(event.target.value.replace(/\D/g, '').slice(0, 4))} />
              {fieldError('expiry') && <span id="demo-card-expiry-error" className="demo-payment-field-error">
                {fieldError('expiry')}
              </span>}
            </label>
            <label className="demo-payment-field">
              <span className="demo-payment-label">{t.cardCvv}</span>
              <input id="demo-card-cvv" type="text" inputMode="numeric" autoComplete="off"
                placeholder="123" value={cvv}
                aria-invalid={Boolean(fieldError('cvv'))}
                aria-describedby={fieldError('cvv') ? 'demo-card-cvv-error' : undefined}
                onBlur={() => markTouched('cvv')}
                onChange={event => setCvv(event.target.value.replace(/\D/g, '').slice(0, 3))} />
              {fieldError('cvv') && <span id="demo-card-cvv-error" className="demo-payment-field-error">
                {fieldError('cvv')}
              </span>}
            </label>
          </div>

          <button className="btn-primary demo-payment-submit" type="submit" disabled={!ready || paying}>
            {paying ? t.paymentProcessing : t.payBtn}
          </button>
        </form>
          </>}
      </section>
    </main>
  </div>;
}
