import { useLang } from '../lib/lang-context';
import { LANGS, LANG_LABELS } from '../lib/i18n';

export default function LangSwitcher() {
  const { lang, setLang } = useLang();
  return (
    <div className="lang-switcher">
      {LANGS.map(l => (
        <button
          key={l}
          className={`lang-btn${lang === l ? ' active' : ''}`}
          onClick={() => setLang(l)}
        >
          {LANG_LABELS[l]}
        </button>
      ))}
    </div>
  );
}