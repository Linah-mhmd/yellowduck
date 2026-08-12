import { useRef, useState } from 'react';

import html2pdf from 'html2pdf.js';

import { cashFlowAPI } from '../services/api';

import { useTranslation } from '../i18n/LanguageContext';

import PageHeader from '../components/PageHeader';

import CashFlowReportPrint from '../components/CashFlowReportPrint';



const RISK_KEYS = { LOW: 'low', MEDIUM: 'medium', HIGH: 'high' };



export default function CashFlowStatus() {

  const { t, lang } = useTranslation();

  const reportRef = useRef(null);

  const [form, setForm] = useState({ avg_inflow: '', avg_outflow: '', growth_rate: '', months: '12', year: '2025' });

  const [file, setFile] = useState(null);

  const [result, setResult] = useState(null);

  const [error, setError] = useState('');

  const [loading, setLoading] = useState(false);

  const [pdfLoading, setPdfLoading] = useState(false);



  const handleSubmit = async (e) => {

    e.preventDefault();

    const hasFile = Boolean(file);

    const hasManual = form.avg_inflow !== '' && form.avg_outflow !== '';

    if (!hasFile && !hasManual) {

      setError(t('cashFlow.needInput'));

      return;

    }

    setLoading(true);

    setError('');

    setResult(null);

    const fd = new FormData();

    if (file) fd.append('file', file);

    fd.append('lang', lang);

    Object.entries(form).forEach(([k, v]) => fd.append(k, v));

    try {

      const { data } = await cashFlowAPI.analyze(fd);

      if (data?.error) {

        throw new Error(data.error);

      }

      if (!data?.result) {

        throw new Error(t('cashFlow.noResult'));

      }

      setResult(data.result);

    } catch (err) {

      setError(err.message || t('cashFlow.analyzeFailed'));

    } finally {

      setLoading(false);

    }

  };



  const chartSrc = (url, b64) => {

    if (b64) return `data:image/png;base64,${b64}`;

    if (!url) return null;

    if (url.startsWith('http') || url.startsWith('data:')) return url;

    return `${window.location.origin}${url}`;

  };



  const waitForImages = async (root) => {

    const imgs = root?.querySelectorAll('img') || [];

    await Promise.all([...imgs].map((img) => {

      if (img.complete && img.naturalWidth) return Promise.resolve();

      return new Promise((resolve) => {

        img.onload = resolve;

        img.onerror = resolve;

      });

    }));

  };



  const downloadPDF = async () => {

    if (!result || !reportRef.current) return;

    setPdfLoading(true);

    setError('');

    try {

      await waitForImages(reportRef.current);

      const opt = {

        margin: [12, 12, 12, 12],

        filename: 'YellowDuck_CashFlow_Report.pdf',

        image: { type: 'jpeg', quality: 0.98 },

        html2canvas: { scale: 2, useCORS: true, logging: false },

        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },

        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },

      };

      await html2pdf().set(opt).from(reportRef.current).save();

    } catch (err) {

      setError(err.message || t('cashFlow.pdfFailed'));

    } finally {

      setPdfLoading(false);

    }

  };



  const clearForm = () => {

    setForm({ avg_inflow: '', avg_outflow: '', growth_rate: '', months: '12', year: '2025' });

    setFile(null);

    setResult(null);

    setError('');

  };



  const prediction = result?.prediction;
  const advice = result?.prediction_advice;
  const isBusinessMode = prediction?.source === 'business' || advice?.analysis_mode === 'business';
  const forecastChartTitle = isBusinessMode
    ? t('cashFlow.outlookChartTitle')
    : t('cashFlow.forecastChartTitle');



  const riskLabel = (level) => {

    const key = RISK_KEYS[level];

    return key ? t(`cashFlow.risk.${key}`) : level;

  };



  const riskClass = (level) => {

    if (level === 'LOW') return 'tag-success';

    if (level === 'HIGH') return 'tag-danger';

    return '';

  };



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

        {loading && <p className="form-note">{t('cashFlow.analyzingHint')}</p>}

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

              {insight.cash_margin_pct != null && (

                <p><strong>{t('cashFlow.cashMargin')}:</strong> {Number(insight.cash_margin_pct).toFixed(1)}%</p>

              )}

              <p className="meta">{insight.advice}</p>

            </div>

          ))}



          {result.graph_url && (

            <div className="chart-preview">

              <h4>{t('cashFlow.chartTitle')}</h4>

              <img src={chartSrc(result.graph_url, result.graph)} alt={t('cashFlow.chartTitle')} crossOrigin="anonymous" />

            </div>

          )}



          {!result.graph_url && result.graph && (

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

                {isBusinessMode && (

                  <p className="form-note">{t('cashFlow.businessModeNote')}</p>

                )}

                <div className="analysis-grid">

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

                  {advice?.projected_monthly_net != null && (

                    <div>

                      <strong>{t('cashFlow.projectedMonthlyNet')}</strong>

                      <p>${Number(advice.projected_monthly_net).toFixed(2)}</p>

                    </div>

                  )}

                  {advice?.runway_months != null && (

                    <div>

                      <strong>{t('cashFlow.runway')}</strong>

                      <p>{advice.runway_months} {t('cashFlow.monthsUnit')}</p>

                    </div>

                  )}

                </div>

                {advice && (

                  <>

                    <p>

                      <strong>{t('cashFlow.riskLevel')}:</strong>{' '}

                      <span className={`tag ${riskClass(advice.risk_level)}`}>

                        {riskLabel(advice.risk_level)}

                      </span>

                    </p>

                    <p className="meta">{advice.advice}</p>

                  </>

                )}

              </div>



              {(prediction.forecast_chart_url || prediction.forecast_chart) && (

                <div className="chart-preview">

                  <h4>{forecastChartTitle}</h4>

                  <img

                    src={chartSrc(prediction.forecast_chart_url, prediction.forecast_chart)}

                    alt={forecastChartTitle}

                    crossOrigin="anonymous"

                  />

                </div>

              )}

            </>

          )}



          <div className="funding-report-pdf-wrap" aria-hidden="true">

            <div ref={reportRef}>

              <CashFlowReportPrint

                form={form}

                result={result}

                prediction={prediction}

                advice={advice}

                t={t}

                lang={lang}

                forecastChartTitle={forecastChartTitle}

              />

            </div>

          </div>



          <button type="button" className="btn btn-primary" onClick={downloadPDF} disabled={pdfLoading}>

            {pdfLoading ? t('cashFlow.downloadingPdf') : t('cashFlow.downloadPdf')}

          </button>

        </div>

      )}

    </div>

  );

}


