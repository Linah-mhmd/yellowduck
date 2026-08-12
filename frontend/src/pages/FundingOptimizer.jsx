import { useRef, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import html2pdf from 'html2pdf.js';
import { fundingAPI } from '../services/api';
import { useTranslation } from '../i18n/LanguageContext';
import PageHeader from '../components/PageHeader';
import FundingReportPrint from '../components/FundingReportPrint';
import { formatStatNumber } from '../utils/format';

ChartJS.register(ArcElement, Tooltip, Legend);

const HEALTH_LABELS = {
  critical: 'healthCritical',
  caution: 'healthCaution',
  stable: 'healthStable',
  growth: 'healthGrowth',
};

const SCENARIO_LABELS = {
  reduce_expenses_10: 'scenarioReduceExpenses',
  increase_revenue_20: 'scenarioIncreaseRevenue',
};

const STAGES = [
  { value: 'idea', labelKey: 'stageIdea' },
  { value: 'seed', labelKey: 'stageSeed' },
  { value: 'growth', labelKey: 'stageGrowth' },
];

function formatDelta(value, lang) {
  const n = Number(value) || 0;
  const formatted = formatStatNumber(Math.abs(n), lang);
  if (n > 0) return `+${formatted}`;
  if (n < 0) return `-${formatted}`;
  return formatted;
}

export default function FundingOptimizer() {
  const { t, lang } = useTranslation();
  const [form, setForm] = useState({
    funding: '',
    capital: '',
    revenue: '',
    expenses: '',
    growth_rate: '',
    duration: '',
    stage: 'seed',
    use_of_funds: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState('');
  const reportRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await fundingAPI.analyze({ ...form, lang });
      setResult(data.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!result || !reportRef.current) return;
    setPdfLoading(true);
    setError('');
    try {
      const filename = 'YellowDuck_Funding_Report.pdf';
      const opt = {
        margin: [12, 12, 12, 12],
        filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      };
      await html2pdf().set(opt).from(reportRef.current).save();
    } catch (err) {
      setError(err.message || 'PDF failed');
    } finally {
      setPdfLoading(false);
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

  const numericFields = [
    ['funding', 'funding.fundingNeeded'],
    ['capital', 'funding.currentCapital'],
    ['revenue', 'funding.monthlyRevenue'],
    ['expenses', 'funding.monthlyExpenses'],
    ['growth_rate', 'funding.growthRate'],
    ['duration', 'funding.duration'],
  ];

  const healthKey = result?.health ? HEALTH_LABELS[result.health] : null;

  return (
    <div className="page-card">
      <PageHeader
        eyebrow={t('funding.eyebrow')}
        title={t('funding.title')}
        subtitle={t('funding.subtitle')}
      />
      <form className="form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          {numericFields.map(([key, labelKey]) => (
            <div className="form-group" key={key}>
              <label>{t(labelKey)}</label>
              <input
                type="number"
                step="0.01"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                required
              />
              {key === 'growth_rate' && (
                <small className="muted" style={{ marginTop: 6, display: 'block' }}>
                  {t('funding.growthRateHint')}
                </small>
              )}
            </div>
          ))}
          <div className="form-group">
            <label>{t('funding.companyStage')}</label>
            <select
              value={form.stage}
              onChange={(e) => setForm({ ...form, stage: e.target.value })}
            >
              {STAGES.map(({ value, labelKey }) => (
                <option key={value} value={value}>{t(`funding.${labelKey}`)}</option>
              ))}
            </select>
          </div>
          <div className="form-group full-width">
            <label>{t('funding.useOfFunds')}</label>
            <textarea
              value={form.use_of_funds}
              onChange={(e) => setForm({ ...form, use_of_funds: e.target.value })}
              rows={3}
              placeholder={t('funding.useOfFundsHint')}
            />
            <small className="muted" style={{ marginTop: 6, display: 'block' }}>
              {t('funding.useOfFundsHint')}
            </small>
          </div>
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? t('funding.analyzing') : t('funding.analyze')}
        </button>
      </form>

      {result && (
        <>
          {result.runway_alert && (
            <div className="runway-alert">
              <strong>{t('funding.runwayAlert')}</strong>
              <p>{result.runway_alert.message}</p>
            </div>
          )}

          <div className="result-card">
            <h3>{t('funding.reportTitle')}</h3>

            {healthKey && (
              <p style={{ marginBottom: 16 }}>
                <strong>{t('funding.health')}:</strong>{' '}
                <span className={`health-badge health-${result.health}`}>
                  {t(`funding.${healthKey}`)}
                </span>
              </p>
            )}

            <h4>{t('funding.businessMetrics')}</h4>
            <div className="result-grid">
              <p><strong>{t('funding.projectedRevenue')}:</strong> {formatStatNumber(result.projected_monthly_revenue, lang)}</p>
              <p><strong>{t('funding.monthlyBurn')}:</strong> {formatStatNumber(result.monthly_burn, lang)}</p>
              <p><strong>{t('funding.runway')}:</strong>{' '}
                {result.runway_months != null ? `${result.runway_months} ${t('funding.months')}` : '—'}
              </p>
              <p><strong>{t('funding.breakEven')}:</strong> {formatStatNumber(result.break_even_revenue, lang)}</p>
              <p><strong>{t('funding.externalNeed')}:</strong> {formatStatNumber(result.external_need, lang)}</p>
              {result.external_need > 0 && result.funding_coverage_pct != null && (
                <p><strong>{t('funding.fundingCoverage')}:</strong> {result.funding_coverage_pct}%</p>
              )}
              {result.funding_surplus > 0 && (
                <p><strong>{t('funding.fundingSurplus')}:</strong> {formatStatNumber(result.funding_surplus, lang)}</p>
              )}
              {result.funding_gap > 0 && (
                <p><strong>{t('funding.fundingGap')}:</strong> {formatStatNumber(result.funding_gap, lang)}</p>
              )}
            </div>

            <div className="result-grid" style={{ marginTop: 16 }}>
              <p>
                <strong>{t('funding.predictedRisk')}:</strong>{' '}
                <span className="highlight">{result.predicted_risk?.toUpperCase()}</span>
              </p>
              <p>
                <strong>{t('funding.profitability')}:</strong> {(result.profitability * 100).toFixed(2)}%
                <small className="muted" style={{ display: 'block', marginTop: 4 }}>
                  {t('funding.profitabilityHint')}
                </small>
              </p>
              <p><strong>{t('funding.stability')}:</strong> {(result.stability * 100).toFixed(2)}%</p>
            </div>

            {result.risk_factors?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <strong>{t('funding.riskFactors')}</strong>
                <ul className="insight-list">
                  {result.risk_factors.map((factor) => (
                    <li key={factor}>{factor}</li>
                  ))}
                </ul>
              </div>
            )}

            {result.scenarios?.length > 0 && (
              <>
                <h4 style={{ marginTop: 24 }}>{t('funding.scenarios')}</h4>
                <div className="scenario-grid">
                  {result.scenarios.map((sc) => (
                    <div key={sc.id} className="scenario-card">
                      <h5>{t(`funding.${SCENARIO_LABELS[sc.id]}`)}</h5>
                      <p><strong>{t('funding.scenarioBurn')}:</strong> {formatStatNumber(sc.monthly_burn, lang)}</p>
                      <p><strong>{t('funding.scenarioRunway')}:</strong>{' '}
                        {sc.runway_months != null ? `${sc.runway_months} ${t('funding.months')}` : '—'}
                      </p>
                      <p><strong>{t('funding.scenarioExternalNeed')}:</strong> {formatStatNumber(sc.external_need, lang)}</p>
                      <p className="scenario-delta">
                        <strong>{t('funding.scenarioChange')}:</strong>{' '}
                        {t('funding.scenarioBurn')} {formatDelta(sc.burn_change, lang)},{' '}
                        {t('funding.scenarioExternalNeed')} {formatDelta(sc.external_need_change, lang)}
                      </p>
                      <span className={`health-badge health-${sc.health}`}>
                        {t(`funding.${HEALTH_LABELS[sc.health]}`)}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}

            <h4 style={{ marginTop: 24 }}>{t('funding.recommendedMix')}</h4>
            <ul>
              <li>{t('funding.equity')}: {result.equity}%</li>
              <li>{t('funding.debt')}: {result.debt}%</li>
              <li>{t('funding.grants')}: {result.grants}%</li>
            </ul>
            <p style={{ marginTop: 16 }}><strong>{t('funding.strategicInsight')}</strong></p>
            <ul className="insight-list">
              {(result.advice_points || [result.advice]).filter(Boolean).map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>
          <div className="funding-report-pdf-wrap" aria-hidden="true">
            <div ref={reportRef}>
              <FundingReportPrint form={form} result={result} t={t} lang={lang} />
            </div>
          </div>
          <div className="chart-container">
            <Pie data={chartData} options={{ plugins: { legend: { position: 'bottom' } } }} />
          </div>
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleDownloadPdf}
              disabled={pdfLoading}
            >
              {pdfLoading ? t('funding.downloadingPdf') : t('funding.downloadPdf')}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
