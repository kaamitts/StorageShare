const API_KEY = import.meta.env.VITE_MAPTILER_API_KEY;

function languageCode(lang) {
  return lang === 'kk' ? 'kk' : lang === 'ru' ? 'ru' : 'en';
}

async function readFeatures(url, signal) {
  if (!API_KEY) throw new Error('mapApiKeyMissing');
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error('mapLookupFailed');
  const data = await response.json();
  return data.features || [];
}

function toPlace(feature) {
  const [longitude, latitude] = feature.center || feature.geometry?.coordinates || [];
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  return { latitude, longitude, address: feature.place_name || feature.text || '' };
}

export async function suggestAddresses(address, lang, signal) {
  const query = new URLSearchParams({
    key: API_KEY || '',
    language: languageCode(lang),
    country: 'kz',
    autocomplete: 'true',
    limit: '5',
  });
  const features = await readFeatures(
    `https://api.maptiler.com/geocoding/${encodeURIComponent(address)}.json?${query}`,
    signal,
  );
  return features.map(toPlace).filter(Boolean);
}

export async function findAddress(address, lang, signal) {
  const [first] = await suggestAddresses(address, lang, signal);
  if (!first) throw new Error('mapAddressNotFound');
  return { ...first, address: first.address || address };
}

export async function findAddressAt(latitude, longitude, lang, signal) {
  const query = new URLSearchParams({
    key: API_KEY || '',
    language: languageCode(lang),
    limit: '1',
  });
  const [first] = await readFeatures(
    `https://api.maptiler.com/geocoding/${longitude},${latitude}.json?${query}`,
    signal,
  );
  if (!first) throw new Error('mapAddressNotFound');
  return first.place_name || first.text || '';
}