import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { logout } from '../api/auth';
import { getSession } from '../api/client';
import { useLang } from '../lib/lang-context';
import LangSwitcher from './LangSwitcher';
export default function Header() {
  const { t } = useLang(); const navigate = useNavigate(); const [busy, setBusy] = useState(false);
  async function signOut() {
    setBusy(true);
    try { await logout(); } catch { /* Local session is still cleared on network failure. */ }
    navigate('/login', { replace: true });
  }
  return <header className="search-header">
    <Link className="search-logo" to="/search">STORAGESHARE</Link>
    <div className="header-actions">
      {getSession()?.user.role === 'partner' && <Link to="/partner">{t.partner}</Link>}
      <LangSwitcher /><button onClick={signOut} disabled={busy}>{t.logout}</button>
    </div>
  </header>;
}
