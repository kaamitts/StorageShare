const LOCALES = { kk: 'kk-KZ', ru: 'ru-RU', en: 'en-GB' };

export function formatMoment(value, lang) {
  return new Date(value).toLocaleString(LOCALES[lang] || 'en-GB', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}