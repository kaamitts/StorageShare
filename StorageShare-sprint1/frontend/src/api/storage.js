import { api } from './client';
export function getDistricts(signal) { return api('/districts/', { signal }); }
export function getStoragePoints(district = '', signal, filters = {}) {
  const params = new URLSearchParams();
  if (district) params.set('district', district);
  if (filters.is24Hours) params.set('is_24_hours', 'true');
  if (filters.openNow) params.set('open_now', 'true');
  const query = params.toString();
  return api(`/storage-points/${query ? `?${query}` : ''}`, { signal });
}
export function getStoragePointById(id, signal) {
  return api(`/storage-points/${encodeURIComponent(id)}/`, { signal });
}

export function createStoragePoint(point, signal) {
  return api('/storage-points/', { method: 'POST', signal, body: point });
}

export function getMyStoragePoints(signal) {
  return api('/partner/storage-points/', { signal });
}
