import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';

export default function CreateProject() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: '', description: '', goals: '', deadline: '',
    contact_email: '', phone: '', status: 'open', amount: '', sector: 'technology',
  });

  const sectors = [
    ['technology', 'fields.technology'],
    ['agriculture', 'fields.agriculture'],
    ['healthcare', 'fields.healthcare'],
    ['education', 'fields.education'],
    ['finance', 'fields.finance'],
    ['industry', 'createProject.sectorIndustry'],
    ['commerce', 'createProject.sectorCommerce'],
    ['general', 'createProject.sectorGeneral'],
  ];
  const [media, setMedia] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    if (media) fd.append('media', media);
    try {
      await projectsAPI.create(fd);
      navigate('/projects');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('createProject.eyebrow')}
        title={t('createProject.title')}
        subtitle={t('createProject.subtitle')}
      />
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label>{t('createProject.projectTitle')} {t('common.required')}</label>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>{t('createProject.deadline')} {t('common.required')}</label>
            <input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} required />
          </div>
          <div className="form-group full-width">
            <label>{t('createProject.description')} {t('common.required')}</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <div className="form-group full-width">
            <label>{t('createProject.goals')}</label>
            <textarea value={form.goals} onChange={(e) => setForm({ ...form, goals: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('createProject.contactEmail')} {t('common.required')}</label>
            <input type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>{t('createProject.phone')}</label>
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('createProject.targetAmount')}</label>
            <input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('createProject.sector')}</label>
            <select value={form.sector} onChange={(e) => setForm({ ...form, sector: e.target.value })}>
              {sectors.map(([val, labelKey]) => (
                <option key={val} value={val}>{t(labelKey)}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>{t('createProject.status')}</label>
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="open">{t('status.open')}</option>
              <option value="in progress">{t('status.inProgress')}</option>
              <option value="closed">{t('status.closed')}</option>
            </select>
          </div>
          <div className="form-group">
            <label>{t('createProject.media')}</label>
            <input type="file" accept="image/*,video/*" onChange={(e) => setMedia(e.target.files[0])} />
          </div>
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? t('createProject.creating') : t('createProject.create')}
        </button>
      </form>
    </div>
  );
}
