import { useState, useEffect, useRef } from 'react';
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
  const { user, refreshUser, loading: authLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [status, setStatus] = useState(tokenFromUrl ? 'verifying' : 'pending');
  const [message, setMessage] = useState('');
  const [devLink, setDevLink] = useState(location.state?.devLink || '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const verifiedRef = useRef(false);

  const isVerified = user?.email_verified === true;

  useEffect(() => {
    if (authLoading || tokenFromUrl) return;
    if (isVerified) setStatus('already_verified');
  }, [authLoading, isVerified, tokenFromUrl]);

  useEffect(() => {
    if (!tokenFromUrl || verifiedRef.current) return;
    verifiedRef.current = true;

    authAPI.verifyEmail(tokenFromUrl)
      .then(({ data }) => {
        setStatus('success');
        setMessage(data.message || t('auth.verifySuccess'));
        refreshUser();
        setTimeout(() => navigate('/poll'), 2500);
      })
      .catch((err) => {
        refreshUser().then(() => {
          setStatus('error');
          setError(err.message || t('auth.verifyFailed'));
        });
      });
  }, [tokenFromUrl, t, refreshUser, navigate]);

  const handleResend = async () => {
    if (isVerified) {
      setStatus('already_verified');
      return;
    }
    setLoading(true);
    setError('');
    setMessage('');
    setDevLink('');
    try {
      const { data } = await authAPI.resendVerification(lang);
      if (data.email_sent) {
        setMessage(t('auth.emailSentSuccess'));
      } else if (data.dev_link) {
        setDevLink(data.dev_link);
        setMessage(t('auth.emailNotConfigured'));
      }
      if (data.error) setError(data.error);
    } catch (err) {
      if (err.message?.includes('already activated') || err.message?.includes('ALREADY_VERIFIED')) {
        setStatus('already_verified');
        refreshUser();
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  if (status === 'verifying' || authLoading) {
    return <LoadingSpinner text={t('common.loading')} />;
  }

  return (
    <div className="page-card">
      <PageHeader
        eyebrow="✉️"
        title={
          status === 'already_verified'
            ? t('auth.alreadyVerified')
            : t('auth.verifyTitle')
        }
        subtitle={
          status === 'success'
            ? message
            : status === 'already_verified'
              ? t('auth.alreadyVerifiedDesc')
              : t('auth.verifyDesc')
        }
      />

      {status === 'success' && (
        <div className="success-message" style={{ textAlign: 'center' }}>
          {message}
        </div>
      )}

      {status === 'already_verified' && (
        <div style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
          <div className="success-message">{t('auth.alreadyVerified')}</div>
          <p className="muted" style={{ marginTop: 16 }}>{t('auth.alreadyVerifiedDesc')}</p>
          <Link to="/" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-block' }}>
            {t('nav.home')} →
          </Link>
        </div>
      )}

      {status === 'error' && (
        <div style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
          <div className="error-message">{error}</div>
          {user && !isVerified && (
            <>
              <p className="muted" style={{ marginTop: 16 }}>{t('auth.checkInbox')}</p>
              <button type="button" className="btn btn-primary" onClick={handleResend} disabled={loading} style={{ marginTop: 16 }}>
                {loading ? t('auth.resending') : t('auth.resendVerification')}
              </button>
            </>
          )}
          {isVerified && (
            <Link to="/" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-block' }}>
              {t('nav.home')} →
            </Link>
          )}
          {!user && (
            <Link to="/login" className="btn btn-primary" style={{ marginTop: 16, display: 'inline-block' }}>
              {t('auth.signIn')}
            </Link>
          )}
        </div>
      )}

      {status === 'pending' && user && !isVerified && (
        <div style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
          <p className="muted" style={{ marginBottom: 24 }}>{t('auth.checkInbox')}</p>
          <p><strong>{user.email}</strong></p>
          {message && <div className="success-message">{message}</div>}
          {devLink && (
            <div className="dev-link-box" style={{ marginTop: 16, padding: 16, background: 'var(--surface-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <p className="meta" style={{ marginBottom: 8 }}>{t('auth.devLink')}:</p>
              <a href={devLink} className="btn btn-secondary" style={{ wordBreak: 'break-all' }}>{devLink}</a>
            </div>
          )}
          {error && <div className="error-message">{error}</div>}
          <button type="button" className="btn btn-primary" onClick={handleResend} disabled={loading} style={{ marginTop: 16 }}>
            {loading ? t('auth.resending') : t('auth.resendVerification')}
          </button>
        </div>
      )}

      {status === 'pending' && !user && (
        <div style={{ textAlign: 'center' }}>
          <Link to="/login" className="btn btn-primary">{t('auth.signIn')}</Link>
        </div>
      )}
    </div>
  );
}
