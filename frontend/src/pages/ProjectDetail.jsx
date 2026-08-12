import { useState, useEffect } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { statusLabel } from '../i18n/helpers';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatMoney } from '../utils/format';

function HealthBar({ score, t }) {
  const color = score >= 70 ? '#28a745' : score >= 40 ? '#ffc107' : '#dc3545';
  return (
    <div className="health-bar-container">
      <div className="health-bar" style={{ width: `${Math.min(score, 100)}%`, background: color }} />
      <span>{score}% {t('projects.health')}</span>
    </div>
  );
}

export default function ProjectDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const showForm = searchParams.get('showForm') === '1' || searchParams.get('view') === '1';
  const { isInvestor } = useAuth();
  const { t } = useTranslation();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [investForm, setInvestForm] = useState({ amount: '', frequency: 'once', currency: 'EGP', share: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id)
      .then(({ data }) => setProject(data.project))
      .catch(() => setProject(null))
      .finally(() => setLoading(false));
  }, [id]);

  const handleInvest = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await projectsAPI.invest(id, investForm);
      setMessage(t('projects.investSubmitted'));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <LoadingSpinner text={t('projects.loadingOne')} />;
  if (!project) return <div className="container"><p>{t('projects.notFound')}</p></div>;

  const isClosed = project.status?.toLowerCase() === 'closed';

  return (
    <div className="container">
      <div className="project-card">
        {project.media_url && (
          <div className="project-image">
            <img src={`/static/${project.media_url}`} alt={project.title} />
          </div>
        )}
        <div className="project-content">
          <h2>{project.title}</h2>
          <p className="muted">{t('projects.by')} {project.founder_name} · {statusLabel(project.status, t)}</p>
          <p><strong>{t('projects.description')}:</strong> {project.description}</p>
          <p><strong>{t('projects.goals')}:</strong> {project.goals}</p>
          <p><strong>{t('projects.deadline')}:</strong> {project.deadline}</p>
          <p><strong>{t('projects.targetAmount')}:</strong> {formatMoney(project.amount, 'EGP')}</p>
          <HealthBar score={project.health_score || 0} t={t} />
          <Link to={`/projects/${id}/feedback`} className="view-btn">{t('projects.viewFeedback')}</Link>
        </div>
      </div>

      {showForm && isInvestor && !isClosed && (
        <form className="form-card" onSubmit={handleInvest} style={{ marginTop: 24 }}>
          <h3>{t('projects.investTitle')}</h3>
          <div className="form-grid">
            <input type="number" placeholder={t('projects.amount')} value={investForm.amount} onChange={(e) => setInvestForm({ ...investForm, amount: e.target.value })} required />
            <select value={investForm.frequency} onChange={(e) => setInvestForm({ ...investForm, frequency: e.target.value })}>
              <option value="once">{t('projects.frequency.once')}</option>
              <option value="monthly">{t('projects.frequency.monthly')}</option>
              <option value="yearly">{t('projects.frequency.yearly')}</option>
            </select>
            <select value={investForm.currency} onChange={(e) => setInvestForm({ ...investForm, currency: e.target.value })}>
              <option value="USD">USD</option>
              <option value="EGP">EGP</option>
              <option value="EUR">EUR</option>
              <option value="SAR">SAR</option>
            </select>
            <input type="number" placeholder={t('projects.share')} value={investForm.share} onChange={(e) => setInvestForm({ ...investForm, share: e.target.value })} required />
          </div>
          <button type="submit" className="invest-btn">{t('projects.submitInvestment')}</button>
          {message && <p className="success-message">{message}</p>}
          {error && <p className="error-message">{error}</p>}
        </form>
      )}

      {showForm && isClosed && <p className="error-message">{t('projects.closedForInvestment')}</p>}
    </div>
  );
}
