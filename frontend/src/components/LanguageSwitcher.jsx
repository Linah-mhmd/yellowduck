import { useTranslation } from '../i18n/LanguageContext';

export default function LanguageSwitcher() {
  const { lang, setLang } = useTranslation();

  return (
    <div className="lang-switcher">
      <button
        type="button"
        className={lang === 'en' ? 'active' : ''}
        onClick={() => setLang('en')}
        aria-label="English"
      >
        EN
      </button>
      <button
        type="button"
        className={lang === 'ar' ? 'active' : ''}
        onClick={() => setLang('ar')}
        aria-label="Arabic"
      >
        ع
      </button>
    </div>
  );
}
