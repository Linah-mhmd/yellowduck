import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { portfolioAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { fieldLabel } from '../i18n/helpers';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';

const FIELD_KEYS = ['Technology', 'Healthcare', 'Education', 'Finance', 'Agriculture', 'Other'];

export default function PortfolioForm() {
  const { id } = useParams();
  const { user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [portfolioId, setPortfolioId] = useState(id || null);
  const [form, setForm] = useState({
    name: '', email: '', experience: 0, fields: [], other_field: '',
    bio: '', business_idea: '', skills: '', short_term_goal: '', long_term_goal: '',
    strengths: '', weaknesses: '', industry_preferences: '', expected_contribution: '',
    linkedin: '', facebook: '', instagram: '',
  });
  const [image, setImage] = useState(null);
  const [cv, setCv] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingForm, setLoadingForm] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      setForm((f) => ({ ...f, name: user.name || '', email: user.email || '' }));
    }
    portfolioAPI.getForm(id)
      .then(({ data }) => {
        if (data.portfolio) {
          setForm((f) => ({ ...f, ...data.portfolio, fields: data.portfolio.fields || [] }));
          setPortfolioId(data.portfolio._id || id);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingForm(false));
  }, [id, user]);

  const toggleField = (field) => {
    setForm((f) => ({
      ...f,
      fields: f.fields.includes(field) ? f.fields.filter((x) => x !== field) : [...f.fields, field],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => {
      if (k === 'fields') fd.append('fields', JSON.stringify(v));
      else fd.append(k, v);
    });
    if (image) fd.append('image', image);
    if (cv) fd.append('cv', cv);
    try {
      await portfolioAPI.save(fd, portfolioId);
      navigate('/portfolio');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loadingForm) return <LoadingSpinner text={t('portfolio.loading')} />;

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('portfolio.eyebrow')}
        title={portfolioId ? t('portfolio.editTitle') : t('portfolio.createTitle')}
        subtitle={t('portfolio.subtitle')}
      />
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group"><label>{t('portfolio.name')}</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></div>
          <div className="form-group"><label>{t('portfolio.email')}</label><input type="email" value={form.email} readOnly style={{ opacity: 0.7 }} /></div>
          <div className="form-group"><label>{t('portfolio.experienceYears')}</label><input type="number" value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value })} /></div>
          <div className="form-group full-width">
            <label>{t('portfolio.preferredFields')}</label>
            <div className="checkbox-group">
              {FIELD_KEYS.map((f) => (
                <label key={f}><input type="checkbox" checked={form.fields.includes(f)} onChange={() => toggleField(f)} /> {fieldLabel(f, t)}</label>
              ))}
            </div>
            {form.fields.includes('Other') && (
              <input placeholder={t('portfolio.otherField')} value={form.other_field} onChange={(e) => setForm({ ...form, other_field: e.target.value })} style={{ marginTop: 12 }} />
            )}
          </div>
          <div className="form-group full-width"><label>{t('portfolio.bio')}</label><textarea value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} /></div>
          <div className="form-group full-width"><label>{t('portfolio.businessIdea')}</label><textarea value={form.business_idea} onChange={(e) => setForm({ ...form, business_idea: e.target.value })} /></div>
          <div className="form-group full-width"><label>{t('portfolio.skills')}</label><textarea value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.shortTerm')}</label><input value={form.short_term_goal} onChange={(e) => setForm({ ...form, short_term_goal: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.longTerm')}</label><input value={form.long_term_goal} onChange={(e) => setForm({ ...form, long_term_goal: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.strengths')}</label><input value={form.strengths} onChange={(e) => setForm({ ...form, strengths: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.weaknesses')}</label><input value={form.weaknesses} onChange={(e) => setForm({ ...form, weaknesses: e.target.value })} /></div>
          <div className="form-group full-width"><label>{t('portfolio.industryPrefs')}</label><input value={form.industry_preferences} onChange={(e) => setForm({ ...form, industry_preferences: e.target.value })} /></div>
          <div className="form-group full-width"><label>{t('portfolio.expectedContribution')}</label><textarea value={form.expected_contribution} onChange={(e) => setForm({ ...form, expected_contribution: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.linkedin')}</label><input value={form.linkedin} onChange={(e) => setForm({ ...form, linkedin: e.target.value })} placeholder="https://linkedin.com/in/..." /></div>
          <div className="form-group"><label>{t('portfolio.facebook')}</label><input value={form.facebook} onChange={(e) => setForm({ ...form, facebook: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.instagram')}</label><input value={form.instagram} onChange={(e) => setForm({ ...form, instagram: e.target.value })} /></div>
          <div className="form-group"><label>{t('portfolio.profileImage')}</label><input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} /></div>
          <div className="form-group"><label>{t('portfolio.cv')}</label><input type="file" accept=".pdf,.doc,.docx" onChange={(e) => setCv(e.target.files[0])} /></div>
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('portfolio.saving') : t('portfolio.save')}</button>
      </form>
    </div>
  );
}
