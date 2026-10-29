import { api, getSession, setSession } from './client';
export async function login(data) {
  const result = await api('/auth/login/', { method: 'POST', body: data, auth: false });
  setSession(result); return result;
}
export async function register(data) {
  const result = await api('/auth/register/', { method: 'POST', body: data, auth: false });
  setSession(result); return result;
}
export async function restoreSession() {
  if (!getSession()) return null;
  const user = await api('/auth/me/');
  if (getSession()) setSession({ ...getSession(), user });
  return user;
}
export async function logout() {
  try {
    const current = getSession();
    if (current) await api('/auth/logout/', { method: 'POST', body: () => ({ refresh: getSession()?.refresh }) });
  } finally { setSession(null); }
}
