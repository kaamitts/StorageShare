function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function login({ email, password }) {
  await delay(600);
  if (password === 'wrong') throw { status: 401 };
  return { token: 'mock-token', user: { id: 1, full_name: 'Test User', email, role: 'traveler' } };
}

export async function register({ full_name, email, password, role }) {
  await delay(600);
  if (email === 'taken@example.com') throw { status: 409 };
  return { token: 'mock-token', user: { id: 2, full_name, email, role } };
}