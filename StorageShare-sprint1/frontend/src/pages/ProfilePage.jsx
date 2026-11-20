import { useEffect, useState } from 'react';
import Header from '../components/Header';
import { getProfile, updateProfile } from '../api/auth';
import { useLang } from '../lib/lang-context';

const PHONE_COUNTRIES = [
  { id: 'kz', dial: '7', digits: 10, label: 'countryKazakhstan' },
  { id: 'kg', dial: '996', digits: 9, label: 'countryKyrgyzstan' },
  { id: 'uz', dial: '998', digits: 9, label: 'countryUzbekistan' },
  { id: 'us', dial: '1', digits: 10, label: 'countryUnitedStates' },
  { id: 'gb', dial: '44', digits: 10, label: 'countryUnitedKingdom' },
  { id: 'tr', dial: '90', digits: 10, label: 'countryTurkey' },
];

function splitPhone(value = '') {
  const digits = value.replace(/\D/g, '');
  if (value.trim().startsWith('+')) {
    const country = [...PHONE_COUNTRIES]
      .sort((a, b) => b.dial.length - a.dial.length)
      .find(item => digits.startsWith(item.dial));
    if (country) return { country: country.id, digits: digits.slice(country.dial.length, country.dial.length + country.digits) };
  }
  const nationalDigits = digits.length === 11 && /^[78]/.test(digits) ? digits.slice(1) : digits;
  return { country: 'kz', digits: nationalDigits.slice(0, 10) };
}

export default function ProfilePage() {
  const { t } = useLang();
  const [state, setState] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ full_name: '', phone_country: 'kz', phone: '' });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getProfile({ signal: controller.signal })
      .then(profile => setState({ profile }))
      .catch(error => {
        if (error.name !== 'AbortError') setState({ error });
      });
    return () => controller.abort();
  }, [attempt]);

  const retry = () => {
    setState({ loading: true });
    setAttempt(value => value + 1);
  };
  function startEditing() {
    const parsedPhone = splitPhone(state.profile.phone || '');
    setForm({
      full_name: state.profile.full_name || '',
      phone_country: parsedPhone.country,
      phone: parsedPhone.digits,
    });
    setSaveError('');
    setSaved(false);
    setEditing(true);
  }
  async function saveProfile(event) {
    event.preventDefault();
    const country = PHONE_COUNTRIES.find(item => item.id === form.phone_country) || PHONE_COUNTRIES[0];
    if (!form.full_name.trim()) {
      setSaveError(t.nameRequired);
      return;
    }
    if (form.phone && form.phone.length !== country.digits) {
      setSaveError(t.phoneDigitsHint.replace('{count}', country.digits));
      return;
    }
    setSaving(true);
    setSaveError('');
    setSaved(false);
    try {
      const phone = form.phone ? `+${country.dial}${form.phone}` : '';
      const profile = await updateProfile({ full_name: form.full_name.trim(), phone });
      setState({ profile });
      setEditing(false);
      setSaved(true);
    } catch {
      setSaveError(t.profileSaveError);
    } finally {
      setSaving(false);
    }
  }
  const { profile } = state;

  return <div className="search-page">
    <Header />
    <main className="search-main profile-main">
      <h1 className="search-title">{t.profile}</h1>
      {state.loading ? <p>{t.loading}</p>
        : state.error ? <div className="profile-message" role="alert">
          <p>{t.requestError}</p>
          <button className="btn-secondary" onClick={retry}>{t.retry}</button>
        </div>
        : <section className="profile-card" aria-label={t.profile}>
          <div className="profile-avatar" aria-hidden="true">
            {(profile.full_name || profile.email).trim().charAt(0).toUpperCase()}
          </div>
          <div className="profile-content">
            {editing ? <form className="profile-edit-form" onSubmit={saveProfile}>
              <label>{t.fullName}
                <input maxLength={120} required value={form.full_name}
                  onChange={event => setForm(current => ({ ...current, full_name: event.target.value }))} />
              </label>
              <label>{t.phone}
                <span className="profile-phone-inputs">
                  <select aria-label={t.phoneCountry} value={form.phone_country}
                    onChange={event => setForm(current => ({
                      ...current,
                      phone_country: event.target.value,
                      phone: current.phone.slice(0, PHONE_COUNTRIES.find(item => item.id === event.target.value).digits),
                    }))}>
                    {PHONE_COUNTRIES.map(country => <option value={country.id} key={country.id}>
                      {t[country.label]} (+{country.dial})
                    </option>)}
                  </select>
                  <input type="tel" inputMode="numeric" autoComplete="tel-national"
                    maxLength={PHONE_COUNTRIES.find(item => item.id === form.phone_country).digits}
                    pattern="[0-9]*" value={form.phone}
                    aria-invalid={Boolean(form.phone) && form.phone.length !== PHONE_COUNTRIES.find(item => item.id === form.phone_country).digits}
                    onChange={event => {
                      const maxDigits = PHONE_COUNTRIES.find(item => item.id === form.phone_country).digits;
                      setForm(current => ({ ...current, phone: event.target.value.replace(/\D/g, '').slice(0, maxDigits) }));
                    }} />
                </span>
                <small>{t.phoneDigitsHint.replace('{count}', PHONE_COUNTRIES.find(item => item.id === form.phone_country).digits)}</small>
              </label>
              {saveError && <p className="profile-form-error" role="alert">{saveError}</p>}
              <div className="profile-actions">
                <button className="btn-primary" type="submit" disabled={saving}>
                  {saving ? t.savingProfile : t.saveProfile}
                </button>
                <button className="btn-secondary" type="button" disabled={saving}
                  onClick={() => setEditing(false)}>{t.cancelEdit}</button>
              </div>
            </form> : <>
              <dl className="profile-details">
                <div><dt>{t.fullName}</dt><dd>{profile.full_name || t.notProvided}</dd></div>
                <div><dt>{t.email}</dt><dd>{profile.email}</dd></div>
                <div><dt>{t.phone}</dt><dd>{profile.phone || t.notProvided}</dd></div>
                <div><dt>{t.accountType}</dt><dd>{profile.role === 'partner' ? t.partner : t.traveler}</dd></div>
                <div><dt>{t.memberSince}</dt><dd>{profile.created_at
                  ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(profile.created_at))
                  : t.notProvided}</dd></div>
              </dl>
              {saved && <p className="profile-saved" role="status">{t.profileSaved}</p>}
              <button className="btn-primary profile-edit-button" type="button" onClick={startEditing}>
                {t.editProfile}
              </button>
            </>}
          </div>
        </section>}
    </main>
  </div>;
}
