import { useState } from 'react';
import { cashFlowAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';

export default function CashFlowStatus() {
  const { t } = useTranslation();
  const [form, setForm] = useState({ avg_inflow: '', avg_outflow: '', growth_rate: '', months: '12', year: '2025' });
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const fd = new FormData();
    if (file) fd.append('file', file);
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    try {
      const { data } = await cashFlowAPI.analyze(fd);
      setResult(data.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    if (!result) return;
    const payload = {
      insights: result.insights,
      prediction: result.prediction,
      prediction_advice: result.prediction_advice,
      chart: result.graph ? `data:image/png;base64,${result.graph}` : null,
      forecast_chart: result.prediction?.forecast_chart
        ? `data:image/png;base64,${result.prediction.forecast_chart}`
        : null,
      user_input: form,
    };
    const { data } = await cashFlowAPI.downloadPDF(payload);
    const url = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'YellowDuck_Financial_Report.pdf';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const clearForm = () => {
    setForm({ avg_inflow: '', avg_outflow: '', growth_rate: '', months: '12', year: '2025' });
    setFile(null);
    setResult(null);
    setError('');
  };

  const prediction = result?.prediction;
  const advice = result?.prediction_advice;

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('cashFlow.eyebrow')}
        title={t('cashFlow.title')}
        subtitle={t('cashFlow.subtitle')}
      />
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>{t('cashFlow.uploadCsv')}</label>
          <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} />
          <p className="form-note">{t('cashFlow.csvHint')}</p>
        </div>
        <div className="form-note">{t('cashFlow.or')}</div>
        <div className="form-grid">
          <div className="form-group">
            <label>{t('cashFlow.avgInflow')}</label>
            <input type="number" step="0.01" value={form.avg_inflow} onChange={(e) => setForm({ ...form, avg_inflow: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('cashFlow.avgOutflow')}</label>
            <input type="number" step="0.01" value={form.avg_outflow} onChange={(e) => setForm({ ...form, avg_outflow: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('cashFlow.growthRate')}</label>
            <input type="number" step="0.01" value={form.growth_rate} onChange={(e) => setForm({ ...form, growth_rate: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('cashFlow.months')}</label>
            <input type="number" value={form.months} onChange={(e) => setForm({ ...form, months: e.target.value })} />
          </div>
          <div className="form-group">
            <label>{t('cashFlow.fiscalYear')}</label>
            <input type="text" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} placeholder="2025" />
          </div>
        </div>
        <div className="button-row">
          <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? t('cashFlow.analyzing') : t('cashFlow.analyze')}</button>
          <button type="button" onClick={clearForm} className="btn btn-secondary">{t('cashFlow.clear')}</button>
        </div>
        {error && <div className="error-message">{error}</div>}
      </form>

      {result && (
        <div className="result-card">
          <h3>{t('cashFlow.insightsTitle')}</h3>
          {result.insights?.map((insight, i) => (
            <div key={i} className="insight-card">
              <h4>{insight.year}</h4>
              <p><strong>{t('cashFlow.trend')}:</strong> <span className={`tag ${insight.trend === 'positive' ? 'tag-success' : 'tag-danger'}`}>{insight.trend === 'positive' ? t('cashFlow.positive') : t('cashFlow.negative')}</span></p>
              <p><strong>{t('cashFlow.avgInflowLabel')}:</strong> ${Number(insight.avg_inflow).toFixed(2)}</p>
              <p><strong>{t('cashFlow.avgOutflowLabel')}:</strong> ${Number(insight.avg_outflow).toFixed(2)}</p>
              <p><strong>{t('cashFlow.avgNet')}:</strong> ${Number(insight.avg_net).toFixed(2)}</p>
              <p className="meta">{insight.advice}</p>
            </div>
          ))}

          {result.graph && (
            <div className="chart-preview">
              <h4>{t('cashFlow.chartTitle')}</h4>
              <img src={`data:image/png;base64,${result.graph}`} alt={t('cashFlow.chartTitle')} />
            </div>
          )}

          {prediction?.warning && (
            <div className="analysis-card">
              <p className="meta text-danger">{prediction.warning}</p>
            </div>
          )}

          {prediction && !prediction.warning && (
            <>
              <div className="analysis-card">
                <h4>{t('cashFlow.predictionTitle')}</h4>
                <div className="analysis-grid">
                  <div>
                    <strong>{t('cashFlow.bestModel')}</strong>
                    <p>{prediction.best_model}</p>
                  </div>
                  <div>
                    <strong>{t('cashFlow.lastEndingBalance')}</strong>
                    <p>${Number(prediction.forecast?.last_ending_balance || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <strong>{t('cashFlow.nextEndingBalance')}</strong>
                    <p>${Number(prediction.forecast?.next_ending_balance || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <strong>{t('cashFlow.expectedChange')}</strong>
                    <p className={prediction.forecast?.change >= 0 ? 'text-success' : 'text-danger'}>
                      ${Number(prediction.forecast?.change || 0).toFixed(2)}
                    </p>
                  </div>
                </div>
                {advice && (
                  <>
                    <p><strong>{t('cashFlow.riskLevel')}:</strong> {advice.risk_level}</p>
                    <p className="meta">{advice.advice}</p>
                  </>
                )}
              </div>

              {prediction.forecast_chart && (
                <div className="chart-preview">
                  <h4>{t('cashFlow.forecastChartTitle')}</h4>
                  <img src={`data:image/png;base64,${prediction.forecast_chart}`} alt={t('cashFlow.forecastChartTitle')} />
                </div>
              )}

              {prediction.model_chart && (
                <div className="chart-preview">
                  <h4>{t('cashFlow.modelChartTitle')}</h4>
                  <img src={`data:image/png;base64,${prediction.model_chart}`} alt={t('cashFlow.modelChartTitle')} />
                </div>
              )}

              {prediction.model_metrics?.length > 0 && (
                <div className="analysis-card">
                  <h4>{t('cashFlow.modelMetricsTitle')}</h4>
                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>{t('cashFlow.modelName')}</th>
                          <th>R²</th>
                          <th>RMSE</th>
                          <th>MAPE (%)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prediction.model_metrics.map((row) => (
                          <tr key={row.model}>
                            <td>{row.model}</td>
                            <td>{row.r2}</td>
                            <td>{row.rmse}</td>
                            <td>{row.mape}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          <button type="button" className="btn btn-primary" onClick={downloadPDF}>{t('cashFlow.downloadPdf')}</button>
        </div>
      )}
    </div>
  );
}
