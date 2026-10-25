import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { validateLogin } from '../lib/validate';
import Field from '../components/Field';
import Button from '../components/Button';
import ErrorBanner from '../components/ErrorBanner';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validateLogin({ email, password });
    if (Object.keys(errs).length) {
      setErrors(errs);
      setBanner('Fill in all required fields.');
      return;
    }
    setErrors({});
    setBanner('');
    setLoading(true);
    try {
      const { user } = await login({ email, password });
      navigate(user.role === 'traveler' ? '/search' : '/partner');
    } catch (err) {
      setPassword('');
      setErrors({ password: 'Wrong email or password' });
      setBanner('Wrong email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Log in</h1>
        <ErrorBanner message={banner} />
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-fields">
            <Field label="Email" type="email" value={email} onChange={setEmail} error={errors.email} placeholder="name@example.com" />
            <Field label="Password" type="password" value={password} onChange={setPassword} error={errors.password} placeholder="········" />
          </div>
          <Button loading={loading}>Log in</Button>
        </form>
        <p className="auth-footer">No account? <a href="/register">Register</a></p>
      </div>
    </div>
  );
}