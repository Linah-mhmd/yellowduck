import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { portfolioAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { roleLabel, statusLabel } from '../i18n/helpers';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatMoney } from '../utils/format';

const PROFILE_FIELD_KEYS = [
  ['short_term_goal', 'portfolio.shortTerm'],
  ['long_term_goal', 'portfolio.longTerm'],
  ['strengths', 'portfolio.strengths'],
  ['weaknesses', 'portfolio.weaknesses'],
  ['industry_preferences', 'portfolio.industryPrefs'],
  ['expected_contribution', 'portfolio.expectedContribution'],
];

function ShareBar({ pct, label }) {
  return (
    <div className="share-bar-wrap">
      <div className="share-bar-header">
        <span>{label}</span>
        <strong>{pct}%</strong>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  );
}

export default function PortfolioView() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('user_email') || user?.email;
  const [profile, setProfile] = useState(null);
  const [investments, setInvestments] = useState([]);
  const [publicTrack, setPublicTrack] = useState([]);
  const [publicProjects, setPublicProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!email) return;
    portfolioAPI.get(email)
      .then(({ data }) => {
        setProfile(data.user);
        setInvestments(data.investments || []);
        setPublicTrack(data.public_track || []);
        setPublicProjects(data.public_projects || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [email]);

  if (loading) return <LoadingSpinner text={t('portfolio.loading')} />;
  if (error) return <div className="container"><div className="error-message">{error}</div></div>;
  if (!profile) return <div className="container"><p>{t('portfolio.notFound')}</p></div>;

  const isOwner = user?.email === profile.email;
  const isInvestor = profile.role?.toLowerCase() === 'investor';
  const isFounder = profile.role?.toLowerCase() === 'founder';

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('portfolio.viewEyebrow')}
        title={t('portfolio.profileOf', { name: profile.name })}
        subtitle={roleLabel(profile.role, t)}
      >
        {isOwner && <Link to="/portfolio/form" className="btn btn-primary" style={{ marginTop: 16 }}>{t('portfolio.editProfile')}</Link>}
      </PageHeader>

      <div className="profile-card form-card">
        {profile.image && (
          <img src={`/static/uploads/${profile.image}`} alt={profile.name} className="profile-avatar" />
        )}
        <div className="profile-grid profile-grid-start">
          <p><strong>{t('portfolio.experience')}:</strong> {profile.experience || 0} {t('portfolio.years')}</p>
          {profile.fields?.length > 0 && <p><strong>{t('portfolio.fields')}:</strong> {profile.fields.join(', ')}</p>}
          {profile.bio && <p><strong>{t('portfolio.bio')}:</strong> {profile.bio}</p>}
          {profile.business_idea && <p><strong>{t('portfolio.businessIdea')}:</strong> {profile.business_idea}</p>}
          {profile.skills && <p><strong>{t('portfolio.skills')}:</strong> {profile.skills}</p>}
          {PROFILE_FIELD_KEYS.map(([key, labelKey]) => profile[key] ? (
            <p key={key}><strong>{t(labelKey)}:</strong> {profile[key]}</p>
          ) : null)}
        </div>

        <div className="social-links">
          {profile.linkedin && <a href={profile.linkedin} target="_blank" rel="noreferrer">LinkedIn</a>}
          {profile.facebook && <a href={profile.facebook} target="_blank" rel="noreferrer">Facebook</a>}
          {profile.instagram && <a href={profile.instagram} target="_blank" rel="noreferrer">Instagram</a>}
          {profile.cv && (
            <a href={`/static/uploads/${profile.cv}`} target="_blank" rel="noreferrer" download>
              {t('portfolio.downloadCv')}
            </a>
          )}
        </div>
      </div>

      {isOwner && isInvestor && investments.length > 0 && (
        <div className="investments-section">
          <h3>{t('portfolio.investments')}</h3>
          {investments.map((inv, i) => (
            <div key={i} className="investment-card">
              <p><strong>{inv.project_title}</strong> — {formatMoney(inv.amount, inv.currency || 'EGP')} ({statusLabel(inv.status, t)})</p>
              <ShareBar pct={inv.share_pct || 0} label={t('portfolio.investmentShare')} />
              <p className="muted">{t('portfolio.founder')}: {inv.founder_name}</p>
            </div>
          ))}
        </div>
      )}

      {!isOwner && isInvestor && publicTrack.length > 0 && (
        <div className="investments-section">
          <h3>{t('portfolio.credibilityTitle')}</h3>
          <p className="meta">{t('portfolio.credibilityDesc')}</p>
          {publicTrack.map((item) => (
            <div key={item.project_id} className="investment-card">
              <p>
                <Link to={`/projects/${item.project_id}`}><strong>{item.project_title}</strong></Link>
                {item.sector && <span className="tag tag-info" style={{ marginInlineStart: 8 }}>{item.sector}</span>}
              </p>
              <ShareBar pct={item.share_pct} label={t('portfolio.investmentShare')} />
              <p className="muted">{t('portfolio.acceptedInvestment')}</p>
            </div>
          ))}
        </div>
      )}

      {!isOwner && isFounder && publicProjects.length > 0 && (
        <div className="investments-section">
          <h3>{t('portfolio.startupProjectsTitle')}</h3>
          <p className="meta">{t('portfolio.startupProjectsDesc')}</p>
          {publicProjects.map((item) => (
            <div key={item.project_id} className="investment-card">
              <p>
                <Link to={`/projects/${item.project_id}`}><strong>{item.project_title}</strong></Link>
                {item.sector && <span className="tag tag-info" style={{ marginInlineStart: 8 }}>{item.sector}</span>}
              </p>
              <ShareBar pct={item.funded_pct} label={t('portfolio.fundedPct')} />
              <p className="muted">
                {t('portfolio.investorCount', { count: item.investor_count })}
                {' · '}
                {statusLabel(item.status, t)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
