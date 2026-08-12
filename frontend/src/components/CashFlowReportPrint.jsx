function Row({ label, value }) {
  return (
    <p className="pdf-row">
      <strong>{label}:</strong> {value}
    </p>
  );
}

function absChartSrc(url, b64) {
  if (b64) return `data:image/png;base64,${b64}`;
  if (!url) return null;
  if (url.startsWith('http') || url.startsWith('data:')) return url;
  if (typeof window !== 'undefined') return `${window.location.origin}${url}`;
  return url;
}

export default function CashFlowReportPrint({ form, result, prediction, advice, t, lang, forecastChartTitle }) {
  const netChart = absChartSrc(result?.graph_url, result?.graph);
  const forecastChart = absChartSrc(
    prediction?.forecast_chart_url,
    prediction?.forecast_chart,
  );
  const insight = result?.insights?.[0];

  return (
    <div className="funding-report-pdf cash-flow-report-pdf" dir={lang === 'ar' ? 'rtl' : 'ltr'} lang={lang}>
      <header className="pdf-header">
        <h1>{t('cashFlow.reportTitle')}</h1>
        <p className="pdf-subtitle">{t('cashFlow.reportSubtitle')}</p>
      </header>

      {form?.avg_inflow !== '' && form?.avg_outflow !== '' && (
        <section className="pdf-section">
          <h2>{t('cashFlow.inputsTitle')}</h2>
          <Row label={t('cashFlow.avgInflow')} value={`$${Number(form.avg_inflow || 0).toFixed(2)}`} />
          <Row label={t('cashFlow.avgOutflow')} value={`$${Number(form.avg_outflow || 0).toFixed(2)}`} />
          {form.growth_rate !== '' && (
            <Row label={t('cashFlow.growthRate')} value={`${form.growth_rate}%`} />
          )}
          <Row label={t('cashFlow.months')} value={form.months || '12'} />
          <Row label={t('cashFlow.fiscalYear')} value={form.year || '—'} />
        </section>
      )}

      {insight && (
        <section className="pdf-section">
          <h2>{t('cashFlow.insightsTitle')}</h2>
          <Row
            label={t('cashFlow.trend')}
            value={insight.trend === 'positive' ? t('cashFlow.positive') : t('cashFlow.negative')}
          />
          <Row label={t('cashFlow.avgInflowLabel')} value={`$${Number(insight.avg_inflow).toFixed(2)}`} />
          <Row label={t('cashFlow.avgOutflowLabel')} value={`$${Number(insight.avg_outflow).toFixed(2)}`} />
          <Row label={t('cashFlow.avgNet')} value={`$${Number(insight.avg_net).toFixed(2)}`} />
          {insight.cash_margin_pct != null && (
            <Row label={t('cashFlow.cashMargin')} value={`${Number(insight.cash_margin_pct).toFixed(1)}%`} />
          )}
          {insight.advice && <p className="meta">{insight.advice}</p>}
        </section>
      )}

      {netChart && (
        <section className="pdf-section pdf-chart-section">
          <h2>{t('cashFlow.chartTitle')}</h2>
          <img src={netChart} alt={t('cashFlow.chartTitle')} crossOrigin="anonymous" className="pdf-chart-img" />
        </section>
      )}

      {prediction && !prediction.warning && (
        <section className="pdf-section">
          <h2>{t('cashFlow.predictionTitle')}</h2>
          <Row
            label={t('cashFlow.lastEndingBalance')}
            value={`$${Number(prediction.forecast?.last_ending_balance || 0).toFixed(2)}`}
          />
          <Row
            label={t('cashFlow.nextEndingBalance')}
            value={`$${Number(prediction.forecast?.next_ending_balance || 0).toFixed(2)}`}
          />
          <Row
            label={t('cashFlow.expectedChange')}
            value={`$${Number(prediction.forecast?.change || 0).toFixed(2)}`}
          />
          {advice?.risk_level && (
            <Row label={t('cashFlow.riskLevel')} value={t(`cashFlow.risk.${advice.risk_level.toLowerCase()}`)} />
          )}
          {advice?.advice && <p className="meta">{advice.advice}</p>}
        </section>
      )}

      {forecastChart && (
        <section className="pdf-section pdf-chart-section">
          <h2>{forecastChartTitle || t('cashFlow.outlookChartTitle')}</h2>
          <img src={forecastChart} alt={forecastChartTitle || t('cashFlow.outlookChartTitle')} crossOrigin="anonymous" className="pdf-chart-img" />
        </section>
      )}
    </div>
  );
}
