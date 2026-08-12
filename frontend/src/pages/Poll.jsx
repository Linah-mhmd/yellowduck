import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { pollAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import { getPollSections, pollOptionLabel } from '../i18n/pollQuestions';
import { roleLabel } from '../i18n/helpers';

function QuestionField({ q, value, onChange, t }) {
  if (q.type === 'textarea') {
    return <textarea name={q.name} value={value} onChange={(e) => onChange(q.name, e.target.value)} required={q.required} />;
  }
  if (q.type === 'select') {
    return (
      <select name={q.name} value={value} onChange={(e) => onChange(q.name, e.target.value)} required={q.required}>
        <option value="">{t('poll.select')}</option>
        {q.options.map((o) => <option key={o} value={o}>{pollOptionLabel(o, t)}</option>)}
      </select>
    );
  }
  return <input type="text" name={q.name} value={value} onChange={(e) => onChange(q.name, e.target.value)} required={q.required} />;
}

export default function Poll() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isFounder = user?.role?.toLowerCase() === 'founder';
  const sections = getPollSections(isFounder, t);

  useEffect(() => {
    pollAPI.get().then(({ data }) => {
      if (data.poll) setAnswers(data.poll);
    }).catch(() => {});
  }, []);

  const handleChange = (name, value) => setAnswers((a) => ({ ...a, [name]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await pollAPI.submit(answers);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="poll-form" onSubmit={handleSubmit}>
      <h2 className="poll-title">{t('poll.title')}</h2>
      <h3 className="poll-subtitle">{t('poll.subtitle', { role: roleLabel(user?.role, t) })}</h3>
      {sections.map((section) => (
        <div key={section.section}>
          <h4>{section.section}</h4>
          {section.items.map((q) => (
            <div key={q.name}>
              <label>{q.label}</label>
              <QuestionField q={q} value={answers[q.name] || ''} onChange={handleChange} t={t} />
            </div>
          ))}
        </div>
      ))}
      {error && <div className="error-message">{error}</div>}
      <button type="submit" className="btn btn-primary" disabled={loading}>
        {loading ? t('poll.saving') : t('poll.submit')}
      </button>
    </form>
  );
}
