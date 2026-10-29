const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
const KEY = 'storageshare.session';
let session = readSession();
let refreshing;
function readSession() {
  try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch { return null; }
}
export function getSession() { return session; }
export function setSession(value) {
  session = value;
  if (value) localStorage.setItem(KEY, JSON.stringify(value));
  else localStorage.removeItem(KEY);
  window.dispatchEvent(new Event('storageshare:session'));
}
export class ApiError extends Error {
  constructor(status, data) {
    super(typeof data?.detail === 'string' ? data.detail : `Request failed (${status})`);
    this.status = status; this.data = data;
  }
}
async function send(path, { body, token, signal, method = 'GET' } = {}) {
  if (typeof body === 'function') body = body();
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method, signal,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError(0, { detail: 'Network error' });
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}
async function refreshAccess() {
  if (!refreshing) {
    const current = session;
    refreshing = (async () => {
      if (!current?.refresh) throw new ApiError(401, null);
      try {
        const tokens = await send('/auth/refresh/', { method: 'POST', body: { refresh: current.refresh } });
        // Do not resurrect a session after logout or replace a newly logged-in account.
        if (session !== current) throw new ApiError(401, null);
        setSession({ ...current, ...tokens });
      } catch (error) {
        if (session === current && error.status === 401) setSession(null);
        throw error;
      }
    })().finally(() => { refreshing = null; });
  }
  return refreshing;
}
export async function api(path, { auth = true, ...options } = {}) {
  const originalToken = auth ? session?.access : undefined;
  try { return await send(path, { ...options, token: originalToken }); }
  catch (error) {
    if (!auth || error.status !== 401) throw error;
    if (!session) throw error;
    if (session.access === originalToken) await refreshAccess();
    try { return await send(path, { ...options, token: session?.access }); }
    catch (retryError) {
      if (retryError.status === 401) setSession(null);
      throw retryError;
    }
  }
}
