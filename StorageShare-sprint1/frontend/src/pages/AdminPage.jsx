import { useEffect, useState } from 'react';
import Header from '../components/Header';
import {
  cancelAdminBooking,
  deleteAdminBooking,
  deleteAdminStoragePoint,
  deleteAdminUser,
  getAdminBookings,
  getAdminDashboard,
  getAdminStoragePoints,
  getAdminUsers,
  setAdminStoragePointActive,
  setAdminUserActive,
} from '../api/admin';
import { districtName } from '../lib/districts';
import { formatMoment } from '../lib/datetime';
import { useLang } from '../lib/lang-context';

const TABS = ['overview', 'bookings', 'storage-points', 'users'];
const BOOKING_STATUS_KEYS = {
  awaiting_payment: 'awaitingPayment',
  expired: 'expired',
  confirmed: 'confirmed',
  checked_in: 'checkedIn',
  completed: 'completed',
  cancelled: 'cancelled',
};
const DISTRICTS = ['alatau', 'almaly', 'auezov', 'bostandyk', 'medeu', 'nauryzbai', 'turksib', 'zhetysu'];

function roleLabel(user, t) {
  return user.role === 'partner' ? t.partner : t.traveler;
}

export default function AdminPage() {
  const { lang, t } = useLang();
  const [tab, setTab] = useState('overview');
  const [searchInput, setSearchInput] = useState('');
  const [filters, setFilters] = useState({ search: '', status: '', district: '', role: '', active: '' });
  const [result, setResult] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    setResult({ loading: true });
    const load = tab === 'overview' ? getAdminDashboard(controller.signal)
      : tab === 'bookings' ? getAdminBookings({ search: filters.search, status: filters.status }, controller.signal)
        : tab === 'storage-points' ? getAdminStoragePoints({
          search: filters.search, district: filters.district, active: filters.active,
        }, controller.signal)
          : getAdminUsers({ search: filters.search, role: filters.role, active: filters.active }, controller.signal);
    load.then(data => setResult({ data }))
      .catch(error => {
        if (error.name !== 'AbortError') setResult({ error });
      });
    return () => controller.abort();
  }, [tab, filters, attempt]);

  function applyFilters(event) {
    event.preventDefault();
    setFilters(current => ({ ...current, search: searchInput.trim() }));
  }

  async function runAction(key, action, confirmation, successText, failureText) {
    if (confirmation && !window.confirm(confirmation)) return;
    setBusy(key);
    setNotice(null);
    try {
      await action();
      setNotice({ type: 'success', text: successText || t.adminActionSuccess });
      setAttempt(value => value + 1);
    } catch (error) {
      const message = error.status === 409 ? failureText : error.data?.detail;
      setNotice({ type: 'error', text: message || t.requestError });
    } finally {
      setBusy('');
    }
  }

  function retry() {
    setResult({ loading: true });
    setAttempt(value => value + 1);
  }

  const data = result.data;
  const isEmptyList = !result.loading && !result.error && Array.isArray(data) && data.length === 0;
  const invalidListResult = tab !== 'overview' && !result.loading && !result.error && !Array.isArray(data);

  return <div className="search-page">
    <Header />
    <main className="search-main admin-main">
      <div className="admin-heading">
        <h1 className="search-title">{t.adminPanel}</h1>
      </div>
      <nav className="admin-tabs" aria-label={t.adminPanel}>
        {TABS.map(value => <button key={value} type="button"
          className={tab === value ? 'admin-tab active' : 'admin-tab'}
          onClick={() => { setResult({ loading: true }); setTab(value); setNotice(null); }}>
          {t[value === 'overview' ? 'adminOverview' : value === 'bookings' ? 'adminBookings'
            : value === 'storage-points' ? 'adminStoragePoints' : 'adminUsers']}
        </button>)}
      </nav>

      {tab !== 'overview' && <form className="admin-filters" onSubmit={applyFilters}>
        <input value={searchInput} onChange={event => setSearchInput(event.target.value)}
          placeholder={tab === 'bookings' ? t.adminBookingSearchPlaceholder : t.adminSearchPlaceholder}
          aria-label={t.adminSearch} />
        {tab === 'bookings' && <select aria-label={t.adminStatusFilter} value={filters.status}
          onChange={event => setFilters(current => ({ ...current, status: event.target.value }))}>
          <option value="">{t.adminAll} — {t.adminStatusFilter}</option>
          {Object.entries(BOOKING_STATUS_KEYS).map(([value, key]) =>
            <option value={value} key={value}>{t[key]}</option>)}
        </select>}
        {tab === 'storage-points' && <>
          <select aria-label={t.adminDistrictFilter} value={filters.district}
            onChange={event => setFilters(current => ({ ...current, district: event.target.value }))}>
            <option value="">{t.adminAll} — {t.adminDistrictFilter}</option>
            {DISTRICTS.map(code => <option value={code} key={code}>{districtName(code, lang)}</option>)}
          </select>
          <select aria-label={t.adminActivityFilter} value={filters.active}
            onChange={event => setFilters(current => ({ ...current, active: event.target.value }))}>
            <option value="">{t.adminAll} — {t.adminActivityFilter}</option>
            <option value="true">{t.pointActive}</option>
            <option value="false">{t.pointInactive}</option>
          </select>
        </>}
        {tab === 'users' && <>
          <select aria-label={t.adminRoleFilter} value={filters.role}
            onChange={event => setFilters(current => ({ ...current, role: event.target.value }))}>
            <option value="">{t.adminAll} — {t.adminRoleFilter}</option>
            <option value="traveler">{t.traveler}</option>
            <option value="partner">{t.partner}</option>
          </select>
          <select aria-label={t.adminActivityFilter} value={filters.active}
            onChange={event => setFilters(current => ({ ...current, active: event.target.value }))}>
            <option value="">{t.adminAll} — {t.adminActivityFilter}</option>
            <option value="true">{t.pointActive}</option>
            <option value="false">{t.pointInactive}</option>
          </select>
        </>}
        <button className="btn-primary admin-search-button" type="submit">{t.adminSearch}</button>
      </form>}

      {notice && <p className={`admin-notice ${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}>
        {notice.text}
      </p>}
      {result.loading ? <p>{t.loading}</p>
        : result.error || invalidListResult ? <div className="admin-empty" role="alert">
          <p>{t.requestError}</p>
          <button className="btn-secondary" onClick={retry}>{t.retry}</button>
        </div>
        : tab === 'overview' ? <section className="admin-stats-grid">
          {[
            [t.adminTotalBookings, data.bookings],
            [t.adminOpenBookings, data.active_bookings],
            [t.adminTotalPoints, data.storage_points],
            [t.adminActivePoints, data.active_storage_points],
            [t.adminTravelers, data.travelers],
            [t.adminPartners, data.partners],
          ].map(([label, value]) => <article className="admin-stat-card" key={label}>
            <span>{label}</span><strong>{value}</strong>
          </article>)}
        </section>
          : isEmptyList ? <p className="admin-empty">{t.adminNoResults}</p>
            : tab === 'bookings' ? <div className="admin-record-list">
              {data.map(booking => <article className="admin-record-card" key={booking.id}>
                <div className="admin-record-heading">
                  <h2>{booking.storage_point_name}</h2>
                  <span className={`point-status ${booking.status}`}>{t[BOOKING_STATUS_KEYS[booking.status]] || booking.status}</span>
                </div>
                <dl className="admin-record-details">
                  <div><dt>{t.bookingNumber}</dt><dd>#{booking.id}</dd></div>
                  <div><dt>{t.fullName}</dt><dd>{booking.traveler_name}</dd></div>
                  <div><dt>{t.email}</dt><dd>{booking.traveler_email}</dd></div>
                  {booking.traveler_phone && <div><dt>{t.phone}</dt><dd>{booking.traveler_phone}</dd></div>}
                  <div><dt>{t.address}</dt><dd>{booking.storage_point_address}, {booking.district}</dd></div>
                  <div><dt>{t.dropOff}</dt><dd>{formatMoment(booking.drop_off_at, lang)}</dd></div>
                  <div><dt>{t.pickUp}</dt><dd>{formatMoment(booking.pick_up_at, lang)}</dd></div>
                  <div><dt>{t.bags}</dt><dd>{booking.bags_count}</dd></div>
                  <div><dt>{t.total}</dt><dd>{booking.total_price} ₸</dd></div>
                </dl>
                <div className="admin-record-actions">
                  {['awaiting_payment', 'confirmed'].includes(booking.status) && <button
                    className="admin-action-button" disabled={Boolean(busy)} onClick={() => runAction(
                      `cancel-booking-${booking.id}`,
                      () => cancelAdminBooking(booking.id),
                      t.adminConfirmCancelBooking, t.adminActionSuccess, t.adminCancelBlocked,
                    )}>{t.adminCancelBooking}</button>}
                  <button className="admin-action-button danger" disabled={Boolean(busy)}
                    onClick={() => runAction(`delete-booking-${booking.id}`,
                      () => deleteAdminBooking(booking.id), t.adminConfirmDeleteBooking)}>
                    {busy === `delete-booking-${booking.id}` ? t.deletingPoint : t.adminDeleteBooking}
                  </button>
                </div>
              </article>)}
            </div>
              : tab === 'storage-points' ? <div className="admin-record-list">
                {data.map(point => <article className="admin-record-card" key={point.id}>
                  <div className="admin-record-heading">
                    <h2>{point.name}</h2>
                    <span className={`point-status ${point.is_active ? 'active' : 'inactive'}`}>
                      {point.is_active ? t.pointActive : t.pointInactive}
                    </span>
                  </div>
                  <dl className="admin-record-details">
                    <div><dt>{t.address}</dt><dd>{point.address}</dd></div>
                    <div><dt>{t.district}</dt><dd>{districtName(point.district, lang, point.district_name)}</dd></div>
                    <div><dt>{t.partner}</dt><dd>{point.partner_name
                      ? `${point.partner_name} · ${point.partner_email}` : point.partner_email}</dd></div>
                    <div><dt>{t.price}</dt><dd>{point.price_per_bag_per_hour} ₸ {t.perBagPerHour}</dd></div>
                    <div><dt>{t.capacityBags}</dt><dd>{point.capacity_bags}</dd></div>
                    <div><dt>{t.workingHours}</dt><dd>{point.is_24_hours
                      ? t.open24Hours : `${point.opens_at} – ${point.closes_at}`}</dd></div>
                    <div><dt>{t.adminPointCount}</dt><dd>{point.bookings_count}</dd></div>
                  </dl>
                  <div className="admin-record-actions">
                    <button className="admin-action-button" disabled={Boolean(busy)}
                      onClick={() => runAction(`active-point-${point.id}`,
                        () => setAdminStoragePointActive(point.id, !point.is_active))}>
                      {point.is_active ? t.adminDeactivate : t.adminActivate}
                    </button>
                    <button className="admin-action-button danger" disabled={Boolean(busy)}
                      onClick={() => runAction(`delete-point-${point.id}`,
                        () => deleteAdminStoragePoint(point.id), t.adminConfirmDeletePoint,
                        t.adminActionSuccess, t.adminDeleteBlockedPoint)}>
                      {busy === `delete-point-${point.id}` ? t.deletingPoint : t.deletePoint}
                    </button>
                  </div>
                </article>)}
              </div>
                : <div className="admin-record-list">
                  {data.map(user => <article className="admin-record-card" key={user.id}>
                    <div className="admin-record-heading">
                      <h2>{user.full_name || user.email}</h2>
                      <span className={`point-status ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? t.pointActive : t.pointInactive}
                      </span>
                    </div>
                    <dl className="admin-record-details">
                      <div><dt>{t.email}</dt><dd>{user.email}</dd></div>
                      {user.phone && <div><dt>{t.phone}</dt><dd>{user.phone}</dd></div>}
                      <div><dt>{t.adminRoleFilter}</dt><dd>{roleLabel(user, t)}</dd></div>
                      <div><dt>{t.adminUserBookings}</dt><dd>{user.bookings_count}</dd></div>
                      <div><dt>{t.adminUserPoints}</dt><dd>{user.storage_points_count}</dd></div>
                      <div><dt>{t.memberSince}</dt><dd>{formatMoment(user.created_at, lang)}</dd></div>
                    </dl>
                    <div className="admin-record-actions">
                      <button className="admin-action-button" disabled={Boolean(busy)}
                        onClick={() => runAction(`active-user-${user.id}`,
                          () => setAdminUserActive(user.id, !user.is_active))}>
                        {user.is_active ? t.adminDeactivate : t.adminActivate}
                      </button>
                      <button className="admin-action-button danger" disabled={Boolean(busy)}
                        onClick={() => runAction(`delete-user-${user.id}`,
                          () => deleteAdminUser(user.id), t.adminConfirmDeleteUser,
                          t.adminActionSuccess, t.adminDeleteBlockedUser)}>
                        {busy === `delete-user-${user.id}` ? t.deletingPoint : t.deletePoint}
                      </button>
                    </div>
                  </article>)}
                </div>}
    </main>
  </div>;
}
