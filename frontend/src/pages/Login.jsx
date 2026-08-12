import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email.trim(), password.trim());
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-visual">
        <div className="hero-blob hero-blob-1" />
        <div className="auth-visual-content">
          <span className="duck-icon">🦆</span>
          <h2>{t('auth.welcomeBack')}</h2>
          <p>{t('auth.welcomeBackDesc')}</p>
        </div>
      </div>
      <div className="auth-form-side">
        <div className="login-container animate-fade-up">
          <h2>{t('auth.signIn')}</h2>
          <p className="auth-subtitle">{t('auth.credentials')}</p>
          <form onSubmit={handleSubmit}>
            <input type="email" placeholder={t('auth.email')} value={email} onChange={(e) => setEmail(e.target.value)} required />
            <input type="password" placeholder={t('auth.password')} value={password} onChange={(e) => setPassword(e.target.value)} required />
            <p className="auth-forgot-link">
              <Link to="/forgot-password">{t('auth.forgotPassword')}</Link>
            </p>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('auth.signingIn') : `${t('auth.signIn')} →`}
            </button>
          </form>
          <p className="auth-footer-link">
            {t('auth.noAccount')} <Link to="/signup">{t('auth.createFree')}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
