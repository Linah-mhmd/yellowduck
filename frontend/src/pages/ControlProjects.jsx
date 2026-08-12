import { useState, useEffect } from 'react';
import { controlAPI, projectsAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ControlProjects() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    controlAPI.list()
      .then(({ data }) => setProjects(data.projects || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const updateField = (index, field, value) => {
    setProjects((prev) => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
  };

  const handleSave = async (project) => {
    setSaving(project._id);
    setMessage('');
    setError('');
    try {
      await projectsAPI.editInline(project._id, {
        title: project.title, status: project.status, deadline: project.deadline,
        description: project.description, goals: project.goals, amount: project.amount,
      });
      setMessage(t('controlProjects.saved', { title: project.title }));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(null);
    }
  };

  const handleDelete = async (project) => {
    if (!window.confirm(t('controlProjects.confirmDelete', { title: project.title }))) return;
    setDeleting(project._id);
    setError('');
    try {
      await projectsAPI.delete(project._id);
      setMessage(t('controlProjects.deleted', { title: project.title }));
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <LoadingSpinner text={t('controlProjects.loading')} />;

  return (
    <div className="container">
      <PageHeader
        eyebrow={t('controlProjects.eyebrow')}
        title={t('controlProjects.title')}
        subtitle={t('controlProjects.subtitle')}
      />

      {message && <div className="success-message">{message}</div>}
      {error && <div className="error-message">{error}</div>}

      {projects.map((project, index) => (
        <div key={project._id} className="project-card control-project-card">
          <div className="control-project-header">
            {project.media_url && (
              <img src={`/static/${project.media_url}`} alt={project.title} className="control-project-thumb" />
            )}
            <div>
              <h3>{project.title}</h3>
              {project.has_investors && (
                <p className="muted">{t('controlProjects.hasInvestors')}</p>
              )}
            </div>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label>{t('controlProjects.titleLabel')}</label>
              <input value={project.title || ''} disabled={project.has_investors}
                onChange={(e) => updateField(index, 'title', e.target.value)} />
            </div>
            <div className="form-group">
              <label>{t('controlProjects.status')}</label>
              <select value={project.status || 'open'} onChange={(e) => updateField(index, 'status', e.target.value)}>
                <option value="open">{t('status.open')}</option>
                <option value="in progress">{t('status.inProgress')}</option>
                <option value="closed">{t('status.closed')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('controlProjects.deadline')}</label>
              <input type="date" value={project.deadline || ''} disabled={project.has_investors}
                onChange={(e) => updateField(index, 'deadline', e.target.value)} />
            </div>
            <div className="form-group">
              <label>{t('controlProjects.amount')}</label>
              <input type="number" value={project.amount || ''} disabled={project.has_investors}
                onChange={(e) => updateField(index, 'amount', e.target.value)} />
            </div>
            <div className="form-group full-width">
              <label>{t('controlProjects.description')}</label>
              <textarea value={project.description || ''} disabled={project.has_investors}
                onChange={(e) => updateField(index, 'description', e.target.value)} />
            </div>
            <div className="form-group full-width">
              <label>{t('controlProjects.goals')}</label>
              <textarea value={project.goals || ''} disabled={project.has_investors}
                onChange={(e) => updateField(index, 'goals', e.target.value)} />
            </div>
          </div>

          <div className="button-row">
            <button className="btn btn-primary" onClick={() => handleSave(project)} disabled={saving === project._id}>
              {saving === project._id ? t('controlProjects.saving') : t('controlProjects.save')}
            </button>
            {project.can_delete && (
              <button className="btn btn-outline btn-danger-outline"
                onClick={() => handleDelete(project)} disabled={deleting === project._id}>
                {deleting === project._id ? t('controlProjects.deleting') : t('controlProjects.delete')}
              </button>
            )}
          </div>
        </div>
      ))}

      {projects.length === 0 && (
        <div className="recommendation-note empty-state">
          <p>{t('controlProjects.empty')}</p>
        </div>
      )}
    </div>
  );
}
