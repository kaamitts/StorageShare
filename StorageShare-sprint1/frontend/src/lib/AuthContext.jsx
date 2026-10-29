import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { getSession } from '../api/client';
import { restoreSession } from '../api/auth';
import { useLang } from './lang-context';
export default function ProtectedRoute({ role }) {
  const { t } = useLang();
  const [session, setCurrent] = useState(getSession);
  const [status, setStatus] = useState('loading');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const sync = () => setCurrent(getSession());
    window.addEventListener('storageshare:session', sync);
    let active = true;
    restoreSession().then(() => { if (active) setStatus('ready'); })
      .catch(error => { if (active) setStatus(error.status === 401 ? 'ready' : 'error'); });
    return () => { active = false; window.removeEventListener('storageshare:session', sync); };
  }, [attempt]);
  if (!session) return <Navigate to="/login" replace />;
  if (status === 'loading') return <p className="search-main">{t.loading}</p>;
  if (status === 'error') return <div className="search-main" role="alert">{t.requestError}<button onClick={() => { setStatus('loading'); setAttempt(a => a + 1); }}>{t.retry}</button></div>;
  if (role && session.user.role !== role) return <Navigate to="/search" replace />;
  return <Outlet />;
}
