const POINTS = [
  { id: 1, name: 'CentralBox', district: { kk: 'Алмалы', ru: 'Алмалинский', en: 'Alatau' }, address: { kk: 'Төле би к-сі, 59', ru: 'ул. Толе би, 59', en: '59 Tole bi St' }, area_m2: 120, price_per_bag_per_day: 500, open_hours: '08:00–22:00', phone: '+7 701 111 22 33' },
  { id: 2, name: 'SafeStore', district: { kk: 'Алмалы', ru: 'Алмалинский', en: 'Alatau' }, address: { kk: 'Фурманов к-сі, 112', ru: 'ул. Фурманова, 112', en: '112 Furmanov St' }, area_m2: 85, price_per_bag_per_day: 450, open_hours: '09:00–21:00', phone: '+7 702 222 33 44' },
  { id: 3, name: 'LuggageHub', district: { kk: 'Бостандық', ru: 'Бостандыкский', en: 'Bostandyk' }, address: { kk: 'Әл-Фараби д-лы, 17', ru: 'пр. Аль-Фараби, 17', en: '17 Al-Farabi Ave' }, area_m2: 200, price_per_bag_per_day: 600, open_hours: '07:00–23:00', phone: '+7 705 333 44 55' },
  { id: 4, name: 'QuickDrop', district: { kk: 'Медеу', ru: 'Медеуский', en: 'Medeu' }, address: { kk: 'Достық д-лы, 291', ru: 'пр. Достык, 291', en: '291 Dostyk Ave' }, area_m2: 60, price_per_bag_per_day: 700, open_hours: '10:00–20:00', phone: '+7 707 444 55 66' },
  { id: 5, name: 'EasyBag', district: { kk: 'Наурызбай', ru: 'Наурызбайский', en: 'Nauryzbay' }, address: { kk: 'Рысқұлов к-сі, 4', ru: 'ул. Рыскулова, 4', en: '4 Ryskulov St' }, area_m2: 95, price_per_bag_per_day: 400, open_hours: '08:00–22:00', phone: '+7 708 555 66 77' },
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
  const kkName = DISTRICTS.kk[districtIndex];
  return POINTS.filter(p => p.district.kk === kkName);
}

export async function getStoragePointById(id) {
  await delay(400);
  const point = POINTS.find(p => p.id === Number(id));
  if (!point) throw { status: 404 };
  return point;
}