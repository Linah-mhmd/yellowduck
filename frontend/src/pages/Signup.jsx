import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTranslation } from '../i18n/LanguageContext';

export default function Signup() {
  const [form, setForm] = useState({
    name: '', email: '', password: '', confirm_password: '', role: 'founder',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const { t, lang } = useTranslation();
  const navigate = useNavigate();

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const validate = () => {
    if (!form.name || !form.email || !form.password || !form.confirm_password || !form.role)
      return t('auth.fillAll');
    if (form.password !== form.confirm_password) return t('auth.passwordMismatch');
    if (form.password.length < 8) return t('auth.passwordMin');
    if (!/[A-Z]/.test(form.password)) return t('auth.passwordUpper');
    if (!/[0-9]/.test(form.password)) return t('auth.passwordNumber');
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }
    setError('');
    setLoading(true);
    try {
      const data = await signup({ ...form, lang });
      navigate(data.redirect || '/verify-email', {
        state: data.dev_link ? { devLink: data.dev_link } : undefined,
      });
    } catch (e) {
      setError(e.message);
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
          <h2>{t('auth.joinTitle')}</h2>
          <p>{t('auth.joinDesc')}</p>
        </div>
      </div>
      <div className="auth-form-side">
        <div className="login-container animate-fade-up">
          <h2>{t('auth.signUp')}</h2>
          <p className="auth-subtitle">{t('auth.joinDesc')}</p>
          <form onSubmit={handleSubmit}>
            <input placeholder={t('auth.fullName')} value={form.name} onChange={(e) => update('name', e.target.value)} required />
            <input type="email" placeholder={t('auth.email')} value={form.email} onChange={(e) => update('email', e.target.value)} required />
            <input type="password" placeholder={t('auth.password')} value={form.password} onChange={(e) => update('password', e.target.value)} required />
            <input type="password" placeholder={t('auth.confirmPassword')} value={form.confirm_password} onChange={(e) => update('confirm_password', e.target.value)} required />
            <select value={form.role} onChange={(e) => update('role', e.target.value)} required>
              <option value="founder">{t('auth.roleFounder')}</option>
              <option value="investor">{t('auth.roleInvestor')}</option>
            </select>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? t('auth.creating') : `${t('auth.signUp')} →`}
            </button>
          </form>
          <p className="auth-footer-link">
            {t('auth.hasAccount')} <Link to="/login">{t('auth.signIn')}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
