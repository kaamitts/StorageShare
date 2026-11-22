const API_KEY = import.meta.env.VITE_MAPTILER_API_KEY;

function languageCode(lang) {
  return lang === 'kk' ? 'kk' : lang === 'ru' ? 'ru' : 'en';
}

async function readFeature(url) {
  if (!API_KEY) throw new Error('mapApiKeyMissing');
  const response = await fetch(url);
  if (!response.ok) throw new Error('mapLookupFailed');
  const data = await response.json();
  const feature = data.features?.[0];
  if (!feature) throw new Error('mapAddressNotFound');
  return feature;
}

export async function findAddress(address, lang) {
  const query = new URLSearchParams({ key: API_KEY || '', language: languageCode(lang), country: 'KZ', limit: '1' });
  const feature = await readFeature(
    `https://api.maptiler.com/geocoding/${encodeURIComponent(address)}.json?${query}`,
  );
  const [longitude, latitude] = feature.center || feature.geometry?.coordinates || [];
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) throw new Error('mapLookupFailed');
  return { latitude, longitude, address: feature.place_name || address };
}

export async function findAddressAt(latitude, longitude, lang) {
  const query = new URLSearchParams({ key: API_KEY || '', language: languageCode(lang), limit: '1' });
  const feature = await readFeature(
    `https://api.maptiler.com/geocoding/${longitude},${latitude}.json?${query}`,
  );
  return feature.place_name || feature.text || '';
}
