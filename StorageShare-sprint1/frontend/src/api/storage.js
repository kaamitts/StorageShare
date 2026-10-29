import { api } from './client';
export function getDistricts(signal) { return api('/districts/', { signal }); }
export function getStoragePoints(district = '', signal) {
  return api(`/storage-points/${district ? `?district=${encodeURIComponent(district)}` : ''}`, { signal });
}
export function getStoragePointById(id, signal) {
  return api(`/storage-points/${encodeURIComponent(id)}/`, { signal });
}
