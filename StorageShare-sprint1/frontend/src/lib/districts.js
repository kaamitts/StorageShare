const names = {
  alatau: ['Алатау', 'Алатауский', 'Alatau'], almaly: ['Алмалы', 'Алмалинский', 'Almaly'],
  auezov: ['Әуезов', 'Ауэзовский', 'Auezov'], bostandyk: ['Бостандық', 'Бостандыкский', 'Bostandyk'],
  medeu: ['Медеу', 'Медеуский', 'Medeu'], nauryzbai: ['Наурызбай', 'Наурызбайский', 'Nauryzbai'],
  turksib: ['Түрксіб', 'Турксибский', 'Turksib'], zhetysu: ['Жетісу', 'Жетысуский', 'Zhetysu'],
};
export function districtName(code, lang, fallback = code) { return names[code]?.[{ kk: 0, ru: 1, en: 2 }[lang]] || fallback; }
