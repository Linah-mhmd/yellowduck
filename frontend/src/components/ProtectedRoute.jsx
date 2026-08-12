import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';
import LoadingSpinner from './LoadingSpinner';

export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth();
  const { t } = useTranslation();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner text={t('common.loading')} />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (role && user.role?.toLowerCase() !== role) {
    return <Navigate to="/" replace />;
  }

  return children;
}
