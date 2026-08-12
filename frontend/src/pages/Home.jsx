import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { homeAPI, statsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import LoadingSpinner from '../components/LoadingSpinner';
import StatCounter from '../components/StatCounter';

const DEFAULT_STATS = {
  total_projects: 0,
  total_investments: 0,
  open_projects: 0,
  total_users: 0,
};

export default function Home() {
  const { user } = useAuth();
  const { t, lang } = useTranslation();
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [stats, setStats] = useState(DEFAULT_STATS);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const features = useMemo(() => [
    { icon: '🎯', title: t('features.matching'), desc: t('features.matchingDesc') },
    { icon: '📈', title: t('features.insights'), desc: t('features.insightsDesc') },
    { icon: '🤝', title: t('features.network'), desc: t('features.networkDesc') },
    { icon: '📊', title: t('features.performance'), desc: t('features.performanceDesc') },
  ], [t]);

  useEffect(() => {
    setLoading(true);
    homeAPI.getData()
      .then(({ data }) => {
        setRecommendations(data.recommendations || []);
        if (data.stats) setStats(data.stats);
      })
      .catch(() => setRecommendations([]))
      .finally(() => setLoading(false));
  }, [user]);

  useEffect(() => {
    statsAPI.get()
      .then(({ data }) => {
        if (data.stats) setStats(data.stats);
      })
      .catch(() => {});
  }, []);

  const statItems = [
    { key: 'total_projects', label: t('home.stats.projects') },
    { key: 'total_investments', label: t('home.stats.investments') },
    { key: 'open_projects', label: t('home.stats.open') },
    { key: 'total_users', label: t('home.stats.members') },
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    if (search.trim()) navigate(`/projects?q=${encodeURIComponent(search.trim())}`);
    else navigate('/projects');
  };

  return (
    <>
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-blob hero-blob-1" />
          <div className="hero-blob hero-blob-2" />
          <div className="hero-blob hero-blob-3" />
          <div className="hero-grid" />
        </div>
        <span className="hero-duck">🦆</span>

        <div className="hero-content animate-fade-up">
          <span className="eyebrow">🦆 {t('home.eyebrow')}</span>
          <h1>
            {t('home.title')}<br />
            <span className="highlight">{t('home.highlight')}</span>
          </h1>
          <p>{t('home.subtitle')}</p>
          <div className="hero-actions">
            <Link to="/projects" className="btn btn-primary">{t('home.explore')} →</Link>
            {!user && <Link to="/signup" className="btn btn-secondary">{t('home.join')}</Link>}
          </div>
          <div className="hero-stats">
            {statItems.map((item, i) => (
              <div key={item.key} className="hero-stat-group">
                {i > 0 && <div className="hero-stat-divider" />}
                <div className="hero-stat">
                  <strong><StatCounter value={stats[item.key]} lang={lang} /></strong>
                  <span>{item.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="search-section">
        <form onSubmit={handleSearch} className="search-bar-inline search-bar-hero">
          <input
            className="search-input"
            type="search"
            placeholder={t('home.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            dir="auto"
          />
          <button type="submit" className="btn btn-primary">{t('home.search')}</button>
        </form>
        <p className="search-hint">{t('home.searchHint')}</p>
      </section>

      <section className="features">
        <div className="section-header animate-fade-up">
          <span className="eyebrow">{t('home.why')}</span>
          <h2>{t('home.designed')}</h2>
          <p>{t('home.designedDesc')}</p>
        </div>
        <div className="feature-boxes">
          {features.map((f, i) => (
            <div key={f.title} className={`feature animate-fade-up animate-delay-${i + 1}`}>
              <div className="feature-icon">{f.icon}</div>
              <strong>{f.title}</strong>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {user && loading && <LoadingSpinner text={t('common.loading')} />}

      {user && !loading && recommendations.length > 0 && (
        <section className="recommendations">
          <div className="section-header">
            <span className="eyebrow">{t('home.personalized')}</span>
            <h2>{t('home.recommended')}</h2>
          </div>
          <div className="recommendation-list">
            {recommendations.map((rec, i) => (
              <div key={rec._id || rec.email || i} className="recommendation-card">
                {user.role?.toLowerCase() === 'investor' ? (
                  <>
                    <h3>{rec.title}</h3>
                    <p>{rec.description?.slice(0, 140)}{rec.description?.length > 140 ? '...' : ''}</p>
                    <p className="muted"><strong>{t('home.founder')}:</strong> {rec.founder_name}</p>
                    <Link to={`/projects/${rec._id}?showForm=1`} className="btn btn-dark">{t('home.viewProject')} →</Link>
                  </>
                ) : (
                  <>
                    <h3>{rec.name}</h3>
                    <p className="muted"><strong>{t('home.email')}:</strong> {rec.email}</p>
                    <p><strong>{t('home.interest')}:</strong> {rec.poll?.q1 || 'N/A'}</p>
                    <Link to={`/portfolio?user_email=${rec.email}`} className="btn btn-dark">{t('home.viewProfile')} →</Link>
                  </>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {user && !loading && recommendations.length === 0 && (
        <section className="recommendations">
          <div className="recommendation-note">
            <span className="eyebrow">{t('home.almostThere')}</span>
            <h2 style={{ marginBottom: 16 }}>{t('home.completeProfile')}</h2>
            <p style={{ marginBottom: 24, color: 'var(--yd-slate)' }}>
              {user.role?.toLowerCase() === 'investor'
                ? t('home.completeInvestor')
                : t('home.completeFounder')}
            </p>
            <Link to={user.role?.toLowerCase() === 'investor' ? '/portfolio' : '/portfolio/form'} className="btn btn-primary">
              {user.role?.toLowerCase() === 'investor' ? t('home.viewProfile') : t('home.updateProfile')}
            </Link>
          </div>
        </section>
      )}

      {!user && (
        <section className="cta-section">
          <div className="cta-content animate-fade-up">
            <h2>{t('home.ctaTitle')}</h2>
            <p>{t('home.ctaDesc')}</p>
            <Link to="/signup" className="btn btn-primary">{t('home.getStarted')} →</Link>
          </div>
        </section>
      )}
    </>
  );
}
