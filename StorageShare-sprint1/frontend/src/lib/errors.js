export function formErrors(error) {
  if (error.status !== 400 || !error.data) return {};
  return Object.fromEntries(Object.entries(error.data).map(([key, value]) =>
    [key, Array.isArray(value) ? value.join(' ') : String(value)]));
}
