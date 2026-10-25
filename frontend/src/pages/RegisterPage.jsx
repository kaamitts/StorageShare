import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../api/auth';
import { validateRegister } from '../lib/validate';
import { useLang } from '../lib/LangContext';
import Field from '../components/Field';
import Button from '../components/Button';
import ErrorBanner from '../components/ErrorBanner';
import LangSwitcher from '../components/LangSwitcher';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { t } = useLang();
  const [full_name, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validateRegister({ full_name, email, password, role }, t);
    if (Object.keys(errs).length) { setErrors(errs); setBanner(t.fillRequired); return; }
    setErrors({}); setBanner(''); setLoading(true);
    try {
      const { user } = await register({ full_name, email, password, role });
      navigate(user.role === 'traveler' ? '/search' : '/partner');
    } catch (err) {
      if (err.status === 409) { setErrors({ email: t.emailTakenField }); setBanner(t.emailTaken); }
    } finally { setLoading(false); }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card-top">
          <h1 className="auth-title">{t.createAccount}</h1>
          <LangSwitcher />
        </div>
        <ErrorBanner message={banner} />
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-fields">
            <Field label={t.fullName} value={full_name} onChange={setFullName} error={errors.full_name} placeholder={t.fullNamePlaceholder} />
            <Field label={t.email} type="email" value={email} onChange={setEmail} error={errors.email} placeholder={t.emailPlaceholder} />
            <Field label={t.password} type="password" value={password} onChange={setPassword} error={errors.password} placeholder={t.minChars} />
            <div>
              <p className="role-label">{t.iAmA}</p>
              <div className="role-row">
                {['traveler', 'partner'].map(r => (
                  <button key={r} type="button"
                    className={`role-btn${role === r ? ' active' : ''}${errors.role ? ' error' : ''}`}
                    onClick={() => setRole(r)}>
                    {r === 'traveler' ? t.traveler : t.partner}
                  </button>
                ))}
              </div>
              {errors.role && <span className="err-msg">! {errors.role}</span>}
            </div>
          </div>
          <Button loading={loading}>{t.registerBtn}</Button>
        </form>
        <p className="auth-footer">{t.haveAccount} <a href="/login">{t.logIn}</a></p>
      </div>
    </div>
  );
}