import { useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { fundingAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function FundingOptimizer() {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    funding: '', capital: '', revenue: '', expenses: '', growth_rate: '', duration: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await fundingAPI.analyze(form);
      setResult(data.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = result ? {
    labels: [t('funding.equity'), t('funding.debt'), t('funding.grants')],
    datasets: [{
      data: [result.equity, result.debt, result.grants],
      backgroundColor: ['#ffca00', '#3d5af8', '#ffd966'],
      borderColor: '#fff',
      borderWidth: 2,
    }],
  } : null;

  const fields = [
    ['funding', 'funding.fundingNeeded'],
    ['capital', 'funding.currentCapital'],
    ['revenue', 'funding.monthlyRevenue'],
    ['expenses', 'funding.monthlyExpenses'],
    ['growth_rate', 'funding.growthRate'],
    ['duration', 'funding.duration'],
  ];

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('funding.eyebrow')}
        title={t('funding.title')}
        subtitle={t('funding.subtitle')}
      />
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          {fields.map(([key, labelKey]) => (
            <div className="form-group" key={key}>
              <label>{t(labelKey)}</label>
              <input type="number" step="0.01" value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} required />
            </div>
          ))}
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? t('funding.analyzing') : t('funding.analyze')}
        </button>
      </form>

      {result && (
        <>
          <div className="result-card">
            <h3>{t('funding.reportTitle')}</h3>
            <div className="result-grid">
              <p><strong>{t('funding.predictedRisk')}:</strong> <span className="highlight">{result.predicted_risk?.toUpperCase()}</span></p>
              <p><strong>{t('funding.profitability')}:</strong> {(result.profitability * 100).toFixed(2)}%</p>
              <p><strong>{t('funding.stability')}:</strong> {(result.stability * 100).toFixed(2)}%</p>
              <p><strong>{t('funding.predictedInflow')}:</strong> <span className="highlight">${Number(result.predicted_inflow).toFixed(2)}</span></p>
            </div>
            <h4>{t('funding.recommendedMix')}</h4>
            <ul>
              <li>{t('funding.equity')}: {result.equity}%</li>
              <li>{t('funding.debt')}: {result.debt}%</li>
              <li>{t('funding.grants')}: {result.grants}%</li>
            </ul>
            <p><strong>{t('funding.strategicInsight')}:</strong> {result.advice}</p>
            <p><strong>{t('funding.aiComment')}:</strong> {result.ai_comment}</p>
          </div>
          <div className="chart-container">
            <Pie data={chartData} options={{ plugins: { legend: { position: 'bottom' } } }} />
          </div>
        </>
      )}
    </div>
  );
}
