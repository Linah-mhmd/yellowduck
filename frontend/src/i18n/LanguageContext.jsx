import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import en from './en';
import ar from './ar';

const translations = { en, ar };

const LanguageContext = createContext(null);

export { LanguageContext };

function getNested(obj, path) {
  return path.split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), obj);
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => localStorage.getItem('yd_lang') || 'en');

  const setLang = useCallback((newLang) => {
    setLangState(newLang);
    localStorage.setItem('yd_lang', newLang);
    document.documentElement.lang = newLang;
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr';
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.body.classList.toggle('rtl', lang === 'ar');
    document.body.classList.toggle('ltr', lang !== 'ar');
    document.title = lang === 'ar'
      ? 'Yellow Duck — استثمر بذكاء'
      : 'Yellow Duck — Invest Smarter';
  }, [lang]);

  const t = useCallback((key, vars = {}) => {
    let str = getNested(translations[lang], key) ?? getNested(translations.en, key) ?? key;
    if (vars && typeof vars === 'object') {
      Object.entries(vars).forEach(([k, v]) => {
        str = String(str).replace(new RegExp(`{{${k}}}`, 'g'), v);
      });
    }
    return str;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, isRTL: lang === 'ar' }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useTranslation must be used within LanguageProvider');
  return ctx;
}
