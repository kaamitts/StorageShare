import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { validateLogin } from '../lib/validate';
import { useLang } from '../lib/LangContext';
import Field from '../components/Field';
import Button from '../components/Button';
import ErrorBanner from '../components/ErrorBanner';
import LangSwitcher from '../components/LangSwitcher';

export default function LoginPage() {
  const navigate = useNavigate();
  const { t } = useLang();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validateLogin({ email, password }, t);
    if (Object.keys(errs).length) { setErrors(errs); setBanner(t.fillRequired); return; }
    setErrors({}); setBanner(''); setLoading(true);
    try {
      const { user } = await login({ email, password });
      navigate(user.role === 'traveler' ? '/search' : '/partner');
    } catch {
      setPassword('');
      setErrors({ password: t.wrongCredentialsField });
      setBanner(t.wrongCredentials);
    } finally { setLoading(false); }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card-top">
          <h1 className="auth-title">{t.logIn}</h1>
          <LangSwitcher />
        </div>
        <ErrorBanner message={banner} />
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-fields">
            <Field label={t.email} type="email" value={email} onChange={setEmail} error={errors.email} placeholder={t.emailPlaceholder} />
            <Field label={t.password} type="password" value={password} onChange={setPassword} error={errors.password} placeholder={t.passwordPlaceholder} />
          </div>
          <Button loading={loading}>{t.loginBtn}</Button>
        </form>
        <p className="auth-footer">{t.noAccount} <a href="/register">{t.register}</a></p>
      </div>
    </div>
  );
}