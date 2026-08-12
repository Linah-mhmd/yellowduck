import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';

export default function ResetPassword() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const navigate = useNavigate();
  const [form, setForm] = useState({ password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authAPI.resetPassword({ token, ...form });
      setMessage(t('auth.resetSuccess'));
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="container">
        <div className="error-message">{t('auth.verifyFailed')}</div>
        <Link to="/forgot-password" className="btn btn-primary">{t('auth.forgotPassword')}</Link>
      </div>
    );
  }

  return (
    <div className="page-card">
      <PageHeader title={t('auth.resetPassword')} subtitle={t('auth.resetDesc')} />
      <form className="form-card" onSubmit={handleSubmit} style={{ maxWidth: 480, margin: '0 auto' }}>
        <div className="form-group">
          <label>{t('auth.newPassword')}</label>
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        </div>
        <div className="form-group">
          <label>{t('auth.confirmPassword')}</label>
          <input type="password" value={form.confirm_password} onChange={(e) => setForm({ ...form, confirm_password: e.target.value })} required />
        </div>
        {error && <div className="error-message">{error}</div>}
        {message && <div className="success-message">{message}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? t('common.loading') : t('auth.updatePassword')}
        </button>
      </form>
    </div>
  );
}
