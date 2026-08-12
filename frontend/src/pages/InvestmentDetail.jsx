import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { investmentAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { statusLabel } from '../i18n/helpers';
import LoadingSpinner from '../components/LoadingSpinner';
import PageHeader from '../components/PageHeader';
import { formatMoney } from '../utils/format';

export default function InvestmentDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    investmentAPI.get(id)
      .then(({ data: res }) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAccept = async () => {
    setActionLoading(true);
    setError('');
    try {
      await investmentAPI.accept(id);
      navigate('/notifications');
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDismiss = async () => {
    setActionLoading(true);
    setError('');
    try {
      await investmentAPI.dismiss(id);
      navigate('/notifications');
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text={t('investment.loading')} />;
  if (error && !data) return <div className="container"><div className="error-message">{error}</div></div>;
  if (!data?.investment) return <div className="container"><p>{t('investment.notFound')}</p></div>;

  const { investment } = data;
  const isPending = investment.status === 'pending';

  return (
    <div className="page-card">
      <PageHeader eyebrow={t('investment.eyebrow')} title={investment.project_title || data.project?.title} />
      <div className="result-card">
        <p><strong>{t('investment.investor')}:</strong> {investment.investor_name || data.investor?.name}</p>
        <p><strong>{t('investment.amount')}:</strong> {formatMoney(investment.amount, investment.currency || 'EGP')}</p>
        <p><strong>{t('investment.share')}:</strong> {investment.share}%</p>
        <p><strong>{t('investment.frequency')}:</strong> {investment.frequency}</p>
        <p><strong>{t('investment.status')}:</strong> <span className="status-badge">{statusLabel(investment.status, t)}</span></p>
      </div>
      {error && <div className="error-message">{error}</div>}
      {isPending && (
        <div className="button-row">
          <button className="btn btn-primary" onClick={handleAccept} disabled={actionLoading}>{t('investment.accept')}</button>
          <button className="btn btn-outline" onClick={handleDismiss} disabled={actionLoading}>{t('investment.dismiss')}</button>
        </div>
      )}
      <Link to="/notifications" className="btn btn-secondary" style={{ marginTop: 16 }}>{t('investment.back')}</Link>
    </div>
  );
}
