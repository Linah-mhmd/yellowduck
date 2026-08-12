import { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { formatLocaleDate, statusLabel } from '../i18n/helpers';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatMoney } from '../utils/format';

function StarRating({ value, onChange, readonly = false }) {
  const [hover, setHover] = useState(0);
  return (
    <div className={`star-rating ${readonly ? 'readonly' : ''}`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={`star ${star <= (hover || value) ? 'active' : ''}`}
          onClick={() => !readonly && onChange?.(star)}
          onMouseEnter={() => !readonly && setHover(star)}
          onMouseLeave={() => !readonly && setHover(0)}
          disabled={readonly}
          aria-label={`${star} stars`}
        >
          ★
        </button>
      ))}
    </div>
  );
}

function getInitials(name = '') {
  return name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase() || '?';
}

export default function Feedback() {
  const { id } = useParams();
  const { t, lang, isRTL } = useTranslation();
  const [data, setData] = useState({ project: null, feedbacks: [], investors: [] });
  const [form, setForm] = useState({ comment: '', rating: 5 });
  const [showAll, setShowAll] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    projectsAPI.feedback.get(id)
      .then(({ data: res }) => setData(res))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setSubmitting(true);
    try {
      await projectsAPI.feedback.submit(id, { comment: form.comment, rating: String(form.rating) });
      setMessage(t('feedback.thankYou'));
      setForm({ comment: '', rating: 5 });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner text={t('feedback.loading')} />;

  const { project, feedbacks, investors } = data;
  const visible = showAll ? feedbacks : feedbacks.slice(0, 3);
  const avgRating = feedbacks.length
    ? (feedbacks.reduce((s, f) => s + (f.rating || 0), 0) / feedbacks.length).toFixed(1)
    : '0.0';

  const backArrow = isRTL ? '→' : '←';

  return (
    <div className="feedback-page">
      <div className="feedback-hero">
        <div className="feedback-hero-bg" />
        <div className="feedback-hero-content animate-fade-up">
          <Link to={`/projects/${id}?view=1`} className="feedback-back-link">{backArrow} {t('feedback.backToProject')}</Link>
          <span className="eyebrow">{t('feedback.eyebrow')}</span>
          <h1>{project?.title}</h1>
          <p className="feedback-hero-meta">
            {t('feedback.by')} <strong>{project?.founder_name}</strong>
            {project?.status && (
              <span className={`status-badge status-${project.status.toLowerCase().replace(' ', '-')}`}>
                {statusLabel(project.status, t)}
              </span>
            )}
          </p>
          <div className="feedback-stats-row">
            <div className="feedback-stat">
              <strong>{avgRating}</strong>
              <StarRating value={Math.round(Number(avgRating))} readonly />
              <span>{t('feedback.avgRating')}</span>
            </div>
            <div className="feedback-stat-divider" />
            <div className="feedback-stat">
              <strong>{feedbacks.length}</strong>
              <span>{t('feedback.totalReviews')}</span>
            </div>
            <div className="feedback-stat-divider" />
            <div className="feedback-stat">
              <strong>{investors.length}</strong>
              <span>{t('feedback.investors')}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="feedback-body">
        <div className="feedback-grid">
          <section className="feedback-section">
            <div className="feedback-section-header">
              <div>
                <h2>{t('feedback.reviews')}</h2>
                <p>{feedbacks.length === 1
                  ? t('feedback.reviewFrom')
                  : t('feedback.reviewsFrom', { count: feedbacks.length })}
                </p>
              </div>
              {feedbacks.length > 3 && (
                <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowAll(!showAll)}>
                  {showAll ? t('feedback.showLess') : t('feedback.viewAll', { count: feedbacks.length })}
                </button>
              )}
            </div>

            {feedbacks.length === 0 ? (
              <div className="feedback-empty">
                <span className="feedback-empty-icon">💬</span>
                <h3>{t('feedback.noReviews')}</h3>
                <p>{t('feedback.beFirst')}</p>
              </div>
            ) : (
              <div className="feedback-cards">
                {visible.map((fb, i) => (
                  <article key={fb._id || i} className="feedback-card-v2 animate-fade-up">
                    <div className="feedback-card-header">
                      <div className="feedback-user">
                        <div className="feedback-avatar">{getInitials(fb.user_name)}</div>
                        <div>
                          <strong>{fb.user_name}</strong>
                          <small>{formatLocaleDate(fb.timestamp, lang)}</small>
                        </div>
                      </div>
                      <div className="feedback-rating-badge">
                        <StarRating value={fb.rating} readonly />
                        <span>{fb.rating}/5</span>
                      </div>
                    </div>
                    <p className="feedback-comment">{fb.comment}</p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <aside className="feedback-sidebar">
            <div className="feedback-form-card">
              <div className="feedback-form-header">
                <span className="feedback-form-icon">✍️</span>
                <div>
                  <h3>{t('feedback.writeReview')}</h3>
                  <p>{t('feedback.shareExperience')}</p>
                </div>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>{t('feedback.yourRating')}</label>
                  <StarRating value={form.rating} onChange={(r) => setForm({ ...form, rating: r })} />
                </div>
                <div className="form-group">
                  <label>{t('feedback.yourComment')}</label>
                  <textarea
                    placeholder={t('feedback.commentPlaceholder')}
                    value={form.comment}
                    onChange={(e) => setForm({ ...form, comment: e.target.value })}
                    required
                    rows={5}
                  />
                </div>
                {message && <div className="success-message">{message}</div>}
                {error && <div className="error-message">{error}</div>}
                <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%' }}>
                  {submitting ? t('feedback.submitting') : `${t('feedback.submitReview')} →`}
                </button>
              </form>
            </div>

            {investors.length > 0 && (
              <div className="investors-panel">
                <div className="investors-panel-header">
                  <span>💰</span>
                  <div>
                    <h3>{t('feedback.investors')}</h3>
                    <p>{investors.length === 1
                      ? t('feedback.activeInvestor')
                      : t('feedback.activeInvestors', { count: investors.length })}
                    </p>
                  </div>
                </div>
                <div className="investors-cards">
                  {investors.map((inv, i) => (
                    <div key={i} className="investor-card-v2">
                      <div className="investor-avatar">{getInitials(inv.name)}</div>
                      <div className="investor-info">
                        <strong>{inv.name}</strong>
                        <p className="investor-amount">{formatMoney(inv.amount, inv.currency || 'EGP')} · {inv.share}% {t('feedback.share')}</p>
                        <Link to={`/portfolio?user_email=${inv.investor_email}`} className="investor-link">
                          {t('feedback.viewProfile')} →
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
