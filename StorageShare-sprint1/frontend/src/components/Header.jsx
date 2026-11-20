import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { logout } from '../api/auth';
import { getSession } from '../api/client';
import { useLang } from '../lib/lang-context';
import LangSwitcher from './LangSwitcher';
import ThemeToggle from './ThemeToggle';
export default function Header() {
  const { t } = useLang(); const navigate = useNavigate(); const [busy, setBusy] = useState(false);
  const role = getSession()?.user.role;
  const isAdmin = Boolean(getSession()?.user.is_admin);
  const canOpenProfile = role === 'traveler' || role === 'partner';
  async function signOut() {
    setBusy(true);
    try { await logout(); } catch {}
    navigate('/login', { replace: true });
  }
  return <header className="search-header">
    <div className="header-brand-group">
      <Link className="search-logo" to="/search">STORAGESHARE</Link>
      {canOpenProfile && <NavLink className={({ isActive }) => `header-nav-link${isActive ? ' active' : ''}`}
        to="/profile">{t.profile}</NavLink>}
    </div>
    <div className="header-actions">
      {role === 'traveler' && <>
        <NavLink className={({ isActive }) => `header-nav-link${isActive ? ' active' : ''}`}
          to="/pending-payment">{t.pendingPayment}</NavLink>
        <NavLink className={({ isActive }) => `header-nav-link${isActive ? ' active' : ''}`}
          to="/history">{t.history}</NavLink>
      </>}
      {isAdmin && <NavLink className={({ isActive }) => `header-nav-link${isActive ? ' active' : ''}`}
        to="/admin">{t.adminPanel}</NavLink>}
      {role === 'partner' && !isAdmin && <NavLink className={({ isActive }) => `header-nav-link${isActive ? ' active' : ''}`}
        to="/partner">{t.partner}</NavLink>}
      <LangSwitcher /><button onClick={signOut} disabled={busy}>{t.logout}</button>
      <ThemeToggle />
    </div>
  </header>;
}
