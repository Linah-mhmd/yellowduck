import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { notificationsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';
import { formatLocaleDate } from '../i18n/helpers';
import LoadingSpinner from '../components/LoadingSpinner';
import PageHeader from '../components/PageHeader';

export default function Notifications() {
  const { refreshUser } = useAuth();
  const { t, lang } = useTranslation();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    notificationsAPI.list()
      .then(({ data }) => {
        setNotifications(data.notifications || []);
        refreshUser();
      })
      .finally(() => setLoading(false));
  }, [refreshUser]);

  if (loading) return <LoadingSpinner text={t('notifications.loading')} />;

  return (
    <div className="container">
      <PageHeader title={t('notifications.title')} />
      {notifications.length === 0 && <p>{t('notifications.empty')}</p>}
      <div className="notifications-list">
        {notifications.map((n) => (
          <div key={n._id} className={`notification-card ${n.read ? 'read' : 'unread'}`}>
            <p>{n.message}</p>
            <small>{formatLocaleDate(n.timestamp, lang)}</small>
            <div className="notification-actions">
              {n.type === 'investment_request' && n.investment_id && (
                <Link to={`/investment/${n.investment_id}`} className="btn btn-primary">{t('notifications.review')}</Link>
              )}
              {n.project_id && (
                <Link to={`/projects/${n.project_id}/feedback`} className="btn btn-secondary">{t('notifications.viewProject')}</Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
