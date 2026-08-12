import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';

export default function ForgotPassword() {
  const { t, lang } = useTranslation();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [devLink, setDevLink] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    setDevLink('');
    try {
      const { data } = await authAPI.forgotPassword(email.trim(), lang);
      setMessage(data.message || t('auth.emailSent'));
      if (data.dev_link) setDevLink(data.dev_link);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-card">
      <PageHeader eyebrow={t('auth.resetPassword')} title={t('auth.forgotPassword')} subtitle={t('auth.forgotDesc')} />
      <form className="form-card" onSubmit={handleSubmit} style={{ maxWidth: 480, margin: '0 auto' }}>
        <div className="form-group">
          <label>{t('auth.email')}</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}
        {devLink && (
          <p className="meta">
            {t('auth.devLink')}: <a href={devLink}>{devLink}</a>
          </p>
        )}
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? t('auth.resending') : t('auth.sendResetLink')}
        </button>
        <p className="auth-footer-link" style={{ marginTop: 16 }}>
          <Link to="/login">{t('auth.signIn')}</Link>
        </p>
      </form>
    </div>
  );
}
