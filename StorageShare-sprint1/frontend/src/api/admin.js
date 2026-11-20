import { api } from './client';

function queryString(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function getAdminDashboard(signal) {
  return api('/admin-panel/dashboard/', { signal });
}

export function getAdminBookings(filters, signal) {
  return api(`/admin-panel/bookings/${queryString(filters)}`, { signal });
}

export function cancelAdminBooking(id) {
  return api(`/admin-panel/bookings/${encodeURIComponent(id)}/cancel/`, { method: 'POST' });
}

export function deleteAdminBooking(id) {
  return api(`/admin-panel/bookings/${encodeURIComponent(id)}/`, { method: 'DELETE' });
}

export function getAdminStoragePoints(filters, signal) {
  return api(`/admin-panel/storage-points/${queryString(filters)}`, { signal });
}

export function setAdminStoragePointActive(id, isActive) {
  return api(`/admin-panel/storage-points/${encodeURIComponent(id)}/active/`, {
    method: 'POST', body: { is_active: isActive },
  });
}

export function deleteAdminStoragePoint(id) {
  return api(`/admin-panel/storage-points/${encodeURIComponent(id)}/`, { method: 'DELETE' });
}

export function getAdminUsers(filters, signal) {
  return api(`/admin-panel/users/${queryString(filters)}`, { signal });
}

export function setAdminUserActive(id, isActive) {
  return api(`/admin-panel/users/${encodeURIComponent(id)}/active/`, {
    method: 'POST', body: { is_active: isActive },
  });
}

export function deleteAdminUser(id) {
  return api(`/admin-panel/users/${encodeURIComponent(id)}/`, { method: 'DELETE' });
}
