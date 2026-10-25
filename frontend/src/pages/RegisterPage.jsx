import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../api/auth';
import { validateRegister } from '../lib/validate';
import Field from '../components/Field';
import Button from '../components/Button';
import ErrorBanner from '../components/ErrorBanner';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [full_name, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('');
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    const errs = validateRegister({ full_name, email, password, role });
    if (Object.keys(errs).length) {
      setErrors(errs);
      setBanner('Fill in all required fields.');
      return;
    }
    setErrors({});
    setBanner('');
    setLoading(true);
    try {
      const { user } = await register({ full_name, email, password, role });
      navigate(user.role === 'traveler' ? '/search' : '/partner');
    } catch (err) {
      if (err.status === 409) {
        setErrors({ email: 'This email is already registered' });
        setBanner('This email is already registered.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Create an account</h1>
        <ErrorBanner message={banner} />
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-fields">
            <Field label="Full name" value={full_name} onChange={setFullName} error={errors.full_name} placeholder="Ivan Petrov" />
            <Field label="Email" type="email" value={email} onChange={setEmail} error={errors.email} placeholder="name@example.com" />
            <Field label="Password" type="password" value={password} onChange={setPassword} error={errors.password} placeholder="min. 8 characters" />
            <div>
              <p className="role-label">I am a</p>
              <div className="role-row">
                {['traveler', 'partner'].map(r => (
                  <button key={r} type="button"
                    className={`role-btn${role === r ? ' active' : ''}${errors.role ? ' error' : ''}`}
                    onClick={() => setRole(r)}>
                    {r === 'traveler' ? 'Traveller' : 'Partner'}
                  </button>
                ))}
              </div>
              {errors.role && <span className="err-msg">! {errors.role}</span>}
            </div>
          </div>
          <Button loading={loading}>Register</Button>
        </form>
        <p className="auth-footer">Already have an account? <a href="/login">Log in</a></p>
      </div>
    </div>
  );
}