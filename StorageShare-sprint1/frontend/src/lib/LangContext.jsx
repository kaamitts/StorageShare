import { useState } from 'react';
import { LangContext } from './lang-context';
import { translations } from './i18n';



export function LangProvider({ children }) {
  const [lang, setLang] = useState('ru');
  const t = translations[lang];
  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}
