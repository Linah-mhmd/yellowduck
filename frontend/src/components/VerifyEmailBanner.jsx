import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';

export default function VerifyEmailBanner() {
  const { user } = useAuth();
  const { t } = useTranslation();

  if (!user || user.email_verified !== false) return null;

  return (
    <div className="verify-banner">
      <span>{t('verify.banner')}</span>
      <Link to="/verify-email">{t('verify.verifyNow')}</Link>
    </div>
  );
}
