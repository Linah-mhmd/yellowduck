import { Link } from 'react-router-dom';
import { useTranslation } from '../i18n/LanguageContext';

export default function NotFound() {
  const { t } = useTranslation();

  return (
    <div className="container not-found-page">
      <span className="not-found-icon">🦆</span>
      <h1>{t('notFound.title')}</h1>
      <p>{t('notFound.desc')}</p>
      <Link to="/" className="btn btn-primary">{t('notFound.back')}</Link>
    </div>
  );
}
