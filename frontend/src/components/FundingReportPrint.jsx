import { formatStatNumber } from '../utils/format';

const STAGE_KEYS = {
  idea: 'stageIdea',
  seed: 'stageSeed',
  growth: 'stageGrowth',
};

const SCENARIO_LABELS = {
  reduce_expenses_10: 'scenarioReduceExpenses',
  increase_revenue_20: 'scenarioIncreaseRevenue',
};

function Row({ label, value }) {
  return (
    <p className="pdf-row">
      <strong>{label}:</strong> {value}
    </p>
  );
}

export default function FundingReportPrint({ form, result, t, lang }) {
  const stageLabel = t(`funding.${STAGE_KEYS[form.stage] || 'stageSeed'}`);
  const advicePoints = (result.advice_points || [result.advice]).filter(Boolean);

  return (
    <div className="funding-report-pdf" dir={lang === 'ar' ? 'rtl' : 'ltr'} lang={lang}>
      <header className="pdf-header">
        <h1>{t('funding.reportTitle')}</h1>
        <p className="pdf-subtitle">{t('funding.reportSubtitle')}</p>
      </header>

      <section className="pdf-section">
        <h2>{t('funding.inputs')}</h2>
        <Row label={t('funding.fundingNeeded')} value={formatStatNumber(form.funding, lang)} />
        <Row label={t('funding.currentCapital')} value={formatStatNumber(form.capital, lang)} />
        <Row label={t('funding.monthlyRevenue')} value={formatStatNumber(form.revenue, lang)} />
        <Row label={t('funding.monthlyExpenses')} value={formatStatNumber(form.expenses, lang)} />
        <Row label={t('funding.growthRate')} value={form.growth_rate} />
        <Row label={t('funding.duration')} value={form.duration} />
        <Row label={t('funding.companyStage')} value={stageLabel} />
        {form.use_of_funds ? (
          <Row label={t('funding.useOfFunds')} value={form.use_of_funds} />
        ) : null}
      </section>

      {result.runway_alert?.message ? (
        <section className="pdf-alert">
          <strong>{t('funding.runwayAlert')}</strong>
          <p>{result.runway_alert.message}</p>
        </section>
      ) : null}

      <section className="pdf-section">
        <h2>{t('funding.businessMetrics')}</h2>
        <Row label={t('funding.projectedRevenue')} value={formatStatNumber(result.projected_monthly_revenue, lang)} />
        <Row label={t('funding.monthlyBurn')} value={formatStatNumber(result.monthly_burn, lang)} />
        <Row
          label={t('funding.runway')}
          value={result.runway_months != null ? `${result.runway_months} ${t('funding.months')}` : '—'}
        />
        <Row label={t('funding.breakEven')} value={formatStatNumber(result.break_even_revenue, lang)} />
        <Row label={t('funding.externalNeed')} value={formatStatNumber(result.external_need, lang)} />
        {result.funding_coverage_pct != null ? (
          <Row label={t('funding.fundingCoverage')} value={`${result.funding_coverage_pct}%`} />
        ) : null}
        {result.funding_surplus > 0 ? (
          <Row label={t('funding.fundingSurplus')} value={formatStatNumber(result.funding_surplus, lang)} />
        ) : null}
      </section>

      <section className="pdf-section">
        <h2>{t('funding.predictedRisk')}</h2>
        <Row label={t('funding.predictedRisk')} value={result.predicted_risk?.toUpperCase()} />
        <Row label={t('funding.profitability')} value={`${(result.profitability * 100).toFixed(2)}%`} />
        <Row label={t('funding.stability')} value={`${(result.stability * 100).toFixed(2)}%`} />
      </section>

      {result.risk_factors?.length > 0 ? (
        <section className="pdf-section">
          <h2>{t('funding.riskFactors')}</h2>
          <ul className="pdf-list">
            {result.risk_factors.map((factor) => (
              <li key={factor}>{factor}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.scenarios?.length > 0 ? (
        <section className="pdf-section">
          <h2>{t('funding.scenarios')}</h2>
          {result.scenarios.map((sc) => (
            <div key={sc.id} className="pdf-scenario">
              <h3>{t(`funding.${SCENARIO_LABELS[sc.id]}`)}</h3>
              <Row label={t('funding.scenarioBurn')} value={formatStatNumber(sc.monthly_burn, lang)} />
              <Row
                label={t('funding.scenarioRunway')}
                value={sc.runway_months != null ? `${sc.runway_months} ${t('funding.months')}` : '—'}
              />
              <Row label={t('funding.scenarioExternalNeed')} value={formatStatNumber(sc.external_need, lang)} />
            </div>
          ))}
        </section>
      ) : null}

      <section className="pdf-section">
        <h2>{t('funding.recommendedMix')}</h2>
        <Row label={t('funding.equity')} value={`${result.equity}%`} />
        <Row label={t('funding.debt')} value={`${result.debt}%`} />
        <Row label={t('funding.grants')} value={`${result.grants}%`} />
      </section>

      {advicePoints.length > 0 ? (
        <section className="pdf-section">
          <h2>{t('funding.strategicInsight')}</h2>
          <ul className="pdf-list">
            {advicePoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
