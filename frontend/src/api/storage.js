const POINTS = [
  { id: 1, name: 'CentralBox', district: { kk: 'Алмалы', ru: 'Алмалинский', en: 'Alatau' }, price_per_bag_per_day: 500 },
  { id: 2, name: 'SafeStore', district: { kk: 'Алмалы', ru: 'Алмалинский', en: 'Alatau' }, price_per_bag_per_day: 450 },
  { id: 3, name: 'LuggageHub', district: { kk: 'Бостандық', ru: 'Бостандыкский', en: 'Bostandyk' }, price_per_bag_per_day: 600 },
  { id: 4, name: 'QuickDrop', district: { kk: 'Медеу', ru: 'Медеуский', en: 'Medeu' }, price_per_bag_per_day: 700 },
  { id: 5, name: 'EasyBag', district: { kk: 'Наурызбай', ru: 'Наурызбайский', en: 'Nauryzbay' }, price_per_bag_per_day: 400 },
];

export const DISTRICTS = {
  kk: ['Алмалы', 'Бостандық', 'Медеу', 'Наурызбай', 'Түркісіб'],
  ru: ['Алмалинский', 'Бостандыкский', 'Медеуский', 'Наурызбайский', 'Турксибский'],
  en: ['Alatau', 'Bostandyk', 'Medeu', 'Nauryzbay', 'Turksib'],
};

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function getDistricts(lang = 'ru') {
  await delay(300);
  return DISTRICTS[lang];
}

export async function getStoragePoints(districtIndex, lang = 'ru') {
  await delay(500);
  if (districtIndex === '' || districtIndex === null || districtIndex === undefined) return POINTS;
  const districtKeys = ['kk', 'ru', 'en'];
  const kkName = DISTRICTS.kk[districtIndex];
  return POINTS.filter(p => p.district.kk === kkName);
}