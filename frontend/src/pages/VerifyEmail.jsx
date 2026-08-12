import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';

export default function VerifyEmail() {
  const { t, lang } = useTranslation();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token');
  const { user, refreshUser } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState(tokenFromUrl ? 'verifying' : 'pending');
  const [message, setMessage] = useState('');
  const [devLink, setDevLink] = useState(location.state?.devLink || '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tokenFromUrl) {
      authAPI.verifyEmail(tokenFromUrl)
        .then(({ data }) => {
          setStatus('success');
          setMessage(data.message || t('auth.verifySuccess'));
          refreshUser();
          setTimeout(() => navigate('/poll'), 2500);
        })
        .catch((err) => {
          setStatus('error');
          setError(err.message || t('auth.verifyFailed'));
        });
    }
  }, [tokenFromUrl, t, refreshUser, navigate]);

  const handleResend = async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await authAPI.resendVerification(lang);
      setMessage(data.message || t('auth.resendVerification'));
      if (data.dev_link) setDevLink(data.dev_link);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (status === 'verifying') return <LoadingSpinner text={t('common.loading')} />;

  return (
    <div className="page-card">
      <PageHeader
        eyebrow="✉️"
        title={t('auth.verifyTitle')}
        subtitle={status === 'success' ? message : t('auth.verifyDesc')}
      />

      {status === 'success' && (
        <div className="success-message" style={{ textAlign: 'center' }}>
          {message}
        </div>
      )}

      {status === 'error' && (
        <div className="error-message">{error}</div>
      )}

      {status === 'pending' && user && user.email_verified === false && (
        <div style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
          <p className="muted" style={{ marginBottom: 24 }}>{t('auth.checkInbox')}</p>
          <p><strong>{user.email}</strong></p>
          {message && <div className="success-message">{message}</div>}
          {error && <div className="error-message">{error}</div>}
          {devLink && (
            <p className="meta">{t('auth.devLink')}: <a href={devLink}>{devLink}</a></p>
          )}
          <button type="button" className="btn btn-primary" onClick={handleResend} disabled={loading} style={{ marginTop: 16 }}>
            {loading ? t('auth.resending') : t('auth.resendVerification')}
          </button>
        </div>
      )}

      {status === 'pending' && (!user || user.email_verified !== false) && (
        <div style={{ textAlign: 'center' }}>
          <Link to="/login" className="btn btn-primary">{t('auth.signIn')}</Link>
        </div>
      )}
    </div>
  );
}
