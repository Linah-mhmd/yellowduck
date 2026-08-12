import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { statusLabel } from '../i18n/helpers';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatMoney } from '../utils/format';

function HealthBar({ score, t }) {
  const color = score >= 70 ? 'var(--yd-success)' : score >= 40 ? 'var(--yd-warning)' : 'var(--yd-danger)';
  return (
    <div className="health-bar-container">
      <div className="health-bar-wrap">
        <div className="health-bar" style={{ width: `${Math.min(score, 100)}%`, background: color }} />
      </div>
      <span>{score}% {t('projects.health')}</span>
    </div>
  );
}

function StatusBadge({ status, t }) {
  const s = status?.toLowerCase() || 'open';
  const cls = s === 'closed' ? 'status-closed' : s === 'in progress' ? 'status-progress' : 'status-open';
  return <span className={`status-badge ${cls}`}>{statusLabel(status, t)}</span>;
}

const FILTERS = ['all', 'open', 'in progress', 'closed'];

export default function Projects() {
  const { t, lang } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchInput, setSearchInput] = useState(query);

  useEffect(() => {
    setSearchInput(query);
  }, [query]);

  useEffect(() => {
    setLoading(true);
    projectsAPI.list(query || undefined, lang)
      .then(({ data }) => setProjects(data.projects || []))
      .finally(() => setLoading(false));
  }, [query, lang]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) setSearchParams({ q: searchInput.trim() });
    else setSearchParams({});
  };

  const filtered = filter === 'all'
    ? projects
    : projects.filter((p) => p.status?.toLowerCase() === filter);

  if (loading) return <LoadingSpinner text={t('projects.loading')} />;

  return (
    <div className="container">
      <PageHeader
        eyebrow={t('projects.eyebrow')}
        title={t('projects.title')}
        subtitle={query ? t('projects.resultsFor', { query }) : t('projects.subtitle')}
      />

      <form onSubmit={handleSearch} className="search-bar-inline">
        <input
          type="search"
          placeholder={t('projects.searchPlaceholder')}
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          dir="auto"
        />
        <button type="submit" className="btn btn-primary">{t('projects.search')}</button>
      </form>
      <p className="search-hint">{t('projects.searchHint')}</p>

      <div className="button-row filter-row">
        {FILTERS.map((f) => (
          <button
            key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? t('status.all') : statusLabel(f, t)}
          </button>
        ))}
      </div>

      <div className="projects-grid">
        {filtered.map((p) => (
          <article key={p._id} className="project-card animate-fade-up">
            {p.media_url ? (
              <div className="project-image">
                <img src={`/static/${p.media_url}`} alt={p.title} loading="lazy" />
                <StatusBadge status={p.status} t={t} />
              </div>
            ) : (
              <div className="project-image project-image-placeholder">
                🚀
                <StatusBadge status={p.status} t={t} />
              </div>
            )}
            <div className="project-content">
              <h2>{p.title}</h2>
              <p className="muted">{t('projects.by')} {p.founder_name}</p>
              <p>{p.description?.slice(0, 120)}{p.description?.length > 120 ? '...' : ''}</p>
              <HealthBar score={p.health_score || 0} t={t} />
              <div className="project-card-footer">
                <span className="project-amount">{formatMoney(p.amount, 'EGP')}</span>
                <span className="muted">{p.feedback_count || 0} {t('projects.reviews')}</span>
              </div>
              <Link to={`/projects/${p._id}?view=1`} className="view-btn project-view-btn">
                {t('projects.viewDetails')} →
              </Link>
            </div>
          </article>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="recommendation-note empty-state">
          <p>{t('projects.noResults')}</p>
        </div>
      )}
    </div>
  );
}
