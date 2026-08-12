# =============================================
# cash_flow.py — Cash Flow Analysis & Ending Balance Prediction
# =============================================

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import io, base64
import matplotlib.cm as cm
import os

from cash_flow_predictor import run_prediction_from_dataframe, _is_official_format

matplotlib.use('Agg')

MONTH_ORDER = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def _dedupe_uppercase_columns(df):
    upper_map = {}
    for col in df.columns:
        key = col.upper().strip()
        if key not in upper_map:
            upper_map[key] = col
    out = df[[upper_map[k] for k in upper_map]].copy()
    out.columns = [c.upper().strip() for c in out.columns]
    return out


def _build_monthly_summary(raw_df):
    """Build monthly inflow/outflow summary from simple or official CSV."""
    if _is_official_format(raw_df):
        df = _dedupe_uppercase_columns(raw_df)
        amount_col = df['AMOUNT']
        if isinstance(amount_col, pd.DataFrame):
            amount_col = amount_col.iloc[:, 0]
        df['AMOUNT'] = pd.to_numeric(amount_col, errors='coerce').fillna(0.0)
        df['MONTH'] = df['MONTH'].astype(str).str.strip().str.title()
        df['FISCAL YEAR'] = df['FISCAL YEAR'].astype(str).str.strip()
        df['INFLOWS/OUTFLOWS'] = df['INFLOWS/OUTFLOWS'].astype(str).str.strip().str.title()
        monthly_summary = (
            df.groupby(['FISCAL YEAR', 'MONTH', 'INFLOWS/OUTFLOWS'])['AMOUNT']
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        monthly_summary = monthly_summary.rename(columns={
            'FISCAL YEAR': 'fiscal year',
            'MONTH': 'month',
        })
    else:
        df = raw_df.copy()
        df.columns = df.columns.str.strip().str.lower()
        required_cols = ['month', 'fiscal year', 'inflows/outflows', 'amount']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f'Missing required column: {col}')
        df = df.dropna(subset=required_cols, how='all')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
        df['month'] = df['month'].astype(str).str.strip().str.title()
        df['fiscal year'] = df['fiscal year'].astype(str).str.strip()
        df['inflows/outflows'] = df['inflows/outflows'].astype(str).str.strip().str.title()
        df = df[(df['month'] != '') & (df['fiscal year'] != '')]
        monthly_summary = (
            df.groupby(['fiscal year', 'month', 'inflows/outflows'])['amount']
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )

    monthly_summary['Total Inflows'] = monthly_summary.filter(regex='(?i)inflow').sum(axis=1)
    monthly_summary['Total Outflows'] = monthly_summary.filter(regex='(?i)outflow').sum(axis=1)
    monthly_summary['Net Cash Flow'] = monthly_summary['Total Inflows'] - monthly_summary['Total Outflows']
    monthly_summary['month'] = pd.Categorical(monthly_summary['month'], categories=MONTH_ORDER, ordered=True)
    monthly_summary = monthly_summary.sort_values(['fiscal year', 'month']).reset_index(drop=True)
    return monthly_summary


def _safe_label(value):
    if value is None:
        return None
    try:
        import pandas as pd
        if pd.isna(value):
            return None
    except ImportError:
        pass
    return str(value)


def _insight_advice(avg_net, avg_in, avg_out, trend, lang='en'):
    margin = (avg_net / avg_in * 100) if avg_in > 0 else 0.0
    if lang == 'ar':
        if trend == 'positive':
            return (
                f'تدفق نقدي إيجابي بمتوسط {avg_net:,.0f}$ شهرياً '
                f'(هامش نقدي {margin:.0f}%). الوضع مناسب للتشغيل والنمو.'
            )
        burn = avg_out - avg_in
        return (
            f'المصروفات تتجاوز الإيرادات بـ {burn:,.0f}$ شهرياً. '
            'راجعي التكاليف الثابتة وسرّعي التحصيل.'
        )
    if trend == 'positive':
        return (
            f'Positive monthly cash flow (~${avg_net:,.0f}, {margin:.0f}% margin). '
            'Healthy for operations and growth.'
        )
    burn = avg_out - avg_in
    return (
        f'Expenses exceed revenue by ~${burn:,.0f}/month. '
        'Review fixed costs and improve collections.'
    )


def _build_insights(monthly_summary, lang='en'):
    insights = []
    for year in monthly_summary['fiscal year'].unique():
        data = monthly_summary[monthly_summary['fiscal year'] == year]
        avg_in = float(data['Total Inflows'].mean()) if 'Total Inflows' in data else 0.0
        avg_out = float(data['Total Outflows'].mean()) if 'Total Outflows' in data else 0.0
        avg_net = float(data['Net Cash Flow'].mean()) if 'Net Cash Flow' in data else 0.0

        try:
            net = data['Net Cash Flow'].dropna()
            if net.empty:
                raise ValueError('no net cash data')
            best_row = data.loc[net.idxmax()]
            worst_row = data.loc[net.idxmin()]
            max_month = _safe_label(best_row['month'])
            max_net = float(best_row['Net Cash Flow'])
            min_month = _safe_label(worst_row['month'])
            min_net = float(worst_row['Net Cash Flow'])
        except Exception:
            max_month = None
            max_net = 0.0
            min_month = None
            min_net = 0.0

        trend = 'positive' if avg_net > 0 else 'negative'
        margin_pct = round((avg_net / avg_in * 100), 1) if avg_in > 0 else 0.0
        insights.append({
            'year': str(year),
            'avg_inflow': round(avg_in, 2),
            'avg_outflow': round(avg_out, 2),
            'avg_net': round(avg_net, 2),
            'cash_margin_pct': margin_pct,
            'trend': trend,
            'max_month': max_month,
            'max_net': round(max_net, 2),
            'min_month': min_month,
            'min_net': round(min_net, 2),
            'advice': _insight_advice(avg_net, avg_in, avg_out, trend, lang),
        })
    return insights


def _build_net_cash_chart(monthly_summary):
    plt.figure(figsize=(7, 3.5))
    years = monthly_summary['fiscal year'].unique().tolist()
    cmap = cm.get_cmap('tab20', max(1, len(years)))
    colors = [cmap(i) for i in range(len(years))]

    for i, year in enumerate(years):
        data_year = monthly_summary[monthly_summary['fiscal year'] == year]
        y_series = pd.to_numeric(data_year['Net Cash Flow'], errors='coerce').fillna(0.0)
        plt.plot(
            data_year['month'].astype(str),
            y_series,
            marker='o',
            color=colors[i],
            linewidth=2,
            label=year,
        )

    plt.title('Monthly Net Cash Flow', fontsize=13, fontweight='bold')
    plt.xlabel('Month')
    plt.ylabel('Net Cash Flow ($)')
    plt.legend(title='Year')
    plt.grid(alpha=0.5)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return graph_base64


def _should_use_business_model(raw_df, manual_data):
    """Use operational forecasting for projections and simple CSV uploads."""
    if manual_data is not None:
        return True
    return not _is_official_format(raw_df)


def _project_next_monthly_net(monthly_summary):
    """Extrapolate next month net from inflow/outflow trend (matches manual growth inputs)."""
    ms = monthly_summary.sort_values(['fiscal year', 'month']).reset_index(drop=True)
    inflows = pd.to_numeric(ms['Total Inflows'], errors='coerce').fillna(0.0)
    outflows = pd.to_numeric(ms['Total Outflows'], errors='coerce').fillna(0.0)
    last_in = float(inflows.iloc[-1])
    last_out = float(outflows.iloc[-1])

    if len(ms) >= 2 and last_in > 0 and last_out > 0:
        first_in = float(inflows.iloc[0])
        first_out = float(outflows.iloc[0])
        steps = max(len(ms) - 1, 1)
        in_step = (last_in / first_in) ** (1 / steps) if first_in > 0 else 1.0
        out_step = (last_out / first_out) ** (1 / steps) if first_out > 0 else 1.0
        next_in = last_in * in_step
        next_out = last_out * out_step
        return float(next_in - next_out)

    nets = pd.to_numeric(ms['Net Cash Flow'], errors='coerce').fillna(0.0)
    if len(nets) >= 2:
        return float(nets.iloc[-1] + (nets.iloc[-1] - nets.iloc[-2]))
    return float(nets.iloc[-1]) if len(nets) else 0.0


def _business_forecast(monthly_summary):
    """Project next-period balance from cumulative net cash flow."""
    ms = monthly_summary.sort_values(['fiscal year', 'month']).reset_index(drop=True)
    nets = pd.to_numeric(ms['Net Cash Flow'], errors='coerce').fillna(0.0)
    if nets.empty:
        return None

    cumulative = nets.cumsum()
    last_balance = float(cumulative.iloc[-1])
    next_net = _project_next_monthly_net(ms)
    next_balance = last_balance + next_net
    change = next_net

    return {
        'forecast': {
            'next_ending_balance': round(next_balance, 2),
            'last_ending_balance': round(last_balance, 2),
            'change': round(change, 2),
            'trend': 'up' if change >= 0 else 'down',
            'projected_monthly_net': round(next_net, 2),
            'last_monthly_net': round(float(nets.iloc[-1]), 2),
        },
        'source': 'business',
    }


def _ml_forecast_reliable(prediction):
    """True when in-sample ML predictions track actual ending balance reasonably."""
    hist = prediction.get('historical') or {}
    actual = hist.get('actual') or []
    predicted = hist.get('predicted') or []
    if len(actual) < 2 or len(predicted) != len(actual):
        return False
    a = pd.Series(actual, dtype=float)
    p = pd.Series(predicted, dtype=float)
    span = max(float(a.max() - a.min()), 1.0)
    return float((a - p).abs().max()) / span <= 0.25


def _build_outlook_chart(monthly_summary, prediction):
    """Monthly net cash flow with a clearly separated projected next period."""
    ms = monthly_summary.sort_values(['fiscal year', 'month']).reset_index(drop=True)
    tail = ms.tail(6).reset_index(drop=True)
    nets = pd.to_numeric(tail['Net Cash Flow'], errors='coerce').fillna(0.0).tolist()
    labels = [f"{str(row['month'])[:3]}" for _, row in tail.iterrows()]

    forecast = (prediction or {}).get('forecast') or {}
    next_net = forecast.get('projected_monthly_net')
    if next_net is None:
        next_net = forecast.get('change')
    next_net = float(next_net) if next_net is not None else None
    last_net = float(nets[-1]) if nets else 0.0

    fig, ax = plt.subplots(figsize=(10, 5))
    hist_x = list(range(len(labels)))
    bar_w = 0.48
    ax.bar(hist_x, nets, color='#3b82f6', alpha=0.88, width=bar_w, label='Monthly Net Cash Flow')

    tick_pos = hist_x[:]
    tick_labels = labels[:]
    if next_net is not None:
        proj_x = len(labels) + 0.75
        ax.bar([proj_x], [next_net], color='#22c55e', alpha=0.95, width=bar_w, label='Projected Next Period')
        ax.axvline(len(labels) - 0.5 + 0.35, color='#cbd5e1', linestyle='--', linewidth=1.2)
        tick_pos.append(proj_x)
        tick_labels.append('Next')

        delta = next_net - last_net
        pct = (delta / abs(last_net) * 100) if last_net else 0.0
        ax.annotate(
            f'{delta:+,.0f}\n({pct:+.1f}%)',
            xy=(proj_x, next_net),
            xytext=(0, 10),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontsize=9,
            fontweight='bold',
            color='#15803d',
        )

    for idx, val in enumerate(nets):
        ax.text(hist_x[idx], val, f'${val:,.0f}', ha='center', va='bottom', fontsize=8, color='#1e3a8a')
    if next_net is not None:
        ax.text(tick_pos[-1], next_net, f'${next_net:,.0f}', ha='center', va='bottom', fontsize=8, color='#15803d')

    ax.axhline(0, color='#888', linewidth=0.8)
    ax.set_xticks(tick_pos, tick_labels, rotation=0)
    ax.set_title('Monthly Net Cash Flow & Outlook (Last 6 Months + Next)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Period')
    ax.set_ylabel('Net Cash Flow ($)')
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.35)
    y_vals = nets + ([next_net] if next_net is not None else [])
    y_max = max(y_vals) if y_vals else 1.0
    y_min = min(0, min(y_vals) if y_vals else 0)
    ax.set_ylim(y_min - abs(y_max) * 0.12, y_max * 1.18)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=80, bbox_inches='tight')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return chart_base64


def _build_business_advice(monthly_summary, prediction, lang='en'):
    if not prediction:
        return None

    forecast = prediction.get('forecast', {})
    avg_net = float(monthly_summary['Net Cash Flow'].mean())
    avg_in = float(monthly_summary['Total Inflows'].mean())
    avg_out = float(monthly_summary['Total Outflows'].mean())
    change = float(forecast.get('change', 0))
    margin_pct = round((avg_net / avg_in * 100), 1) if avg_in > 0 else 0.0

    burn = max(0.0, avg_out - avg_in)
    last_bal = float(forecast.get('last_ending_balance', 0))
    runway = round(last_bal / burn, 1) if burn > 0 and last_bal > 0 else None

    if avg_net > 0 and change >= 0:
        risk_level = 'LOW'
        if lang == 'ar':
            advice = (
                f'تدفق نقدي إيجابي ({avg_net:,.0f}$/شهر، هامش {margin_pct}%). '
                'الرصيد التراكمي متوقع أن ينمو في الفترة القادمة — استمري في ضبط المصروفات والتحصيل.'
            )
        else:
            advice = (
                f'Positive cash flow (${avg_net:,.0f}/month, {margin_pct}% margin). '
                'Cumulative balance is projected to grow next period — maintain cost control and collections.'
            )
    elif avg_net > 0 and change < 0:
        risk_level = 'MEDIUM'
        if lang == 'ar':
            advice = (
                'صافي شهري إيجابي لكن الرصيد قد ينخفض قليلاً — راقبي المصروفات الكبيرة والتزامات الدفع.'
            )
        else:
            advice = (
                'Monthly net is positive but balance may dip slightly — watch large outflows and payment timing.'
            )
    elif avg_net <= 0:
        risk_level = 'HIGH'
        runway_note = ''
        if runway is not None:
            runway_note = (
                f' المدى التشغيلي التقريبي: {runway} شهر.'
                if lang == 'ar'
                else f' Estimated runway: ~{runway} months.'
            )
        if lang == 'ar':
            advice = (
                f'حرق نقدي بـ {burn:,.0f}$ شهرياً.{runway_note} '
                'قلّلي التكاليف أو زيدي الإيرادات بشكل عاجل.'
            )
        else:
            advice = (
                f'Cash burn of ~${burn:,.0f}/month.{runway_note} '
                'Reduce costs or increase revenue urgently.'
            )
    else:
        risk_level = 'MEDIUM'
        advice = (
            'راقبي التدفقات الشهرية عن كثب.'
            if lang == 'ar'
            else 'Monitor monthly inflows and outflows closely.'
        )

    return {
        'next_ending_balance': forecast.get('next_ending_balance', 0),
        'last_ending_balance': forecast.get('last_ending_balance', 0),
        'change': change,
        'trend': forecast.get('trend', 'down'),
        'projected_monthly_net': forecast.get('projected_monthly_net'),
        'cash_margin_pct': margin_pct,
        'runway_months': runway,
        'risk_level': risk_level,
        'advice': advice,
        'analysis_mode': 'business',
    }


def _build_prediction_advice(prediction, monthly_summary=None, lang='en'):
    """Derive business advice from ending-balance forecast (ML or operational)."""
    if not prediction or prediction.get('warning'):
        return None

    if prediction.get('source') == 'business' and monthly_summary is not None:
        return _build_business_advice(monthly_summary, prediction, lang)

    forecast = prediction.get('forecast', {})
    change = float(forecast.get('change', 0))
    trend = forecast.get('trend', 'down')
    next_balance = forecast.get('next_ending_balance', 0)
    last_balance = forecast.get('last_ending_balance', 0)

    avg_net = None
    if monthly_summary is not None:
        avg_net = float(monthly_summary['Net Cash Flow'].mean())
        if avg_net > 0 and change < 0:
            business_pred = _business_forecast(monthly_summary)
            if business_pred and business_pred['forecast'].get('change', 0) >= 0:
                business_pred['forecast_chart'] = prediction.get('forecast_chart')
                return _build_business_advice(monthly_summary, business_pred, lang)

    if trend == 'up' and change > 0:
        risk_level = 'LOW'
        advice = (
            'الرصيد المتوقع في نمو — حافظي على إدارة النقد الحالية.'
            if lang == 'ar'
            else 'Balance is projected to rise — maintain current cash management.'
        )
    elif abs(change) < max(abs(last_balance) * 0.05, 1):
        risk_level = 'MEDIUM'
        advice = (
            'الرصيد مستقر نسبياً — راقبي التدفقات الداخلة والخارجة.'
            if lang == 'ar'
            else 'Balance is relatively stable — monitor inflows and outflows closely.'
        )
    else:
        risk_level = 'HIGH'
        advice = (
            'قد ينخفض الرصيد — قلّلي التكاليف وحسّني التحصيل.'
            if lang == 'ar'
            else 'Balance may decline — reduce costs and improve collections.'
        )

    return {
        'next_ending_balance': next_balance,
        'last_ending_balance': last_balance,
        'change': change,
        'trend': trend,
        'risk_level': risk_level,
        'advice': advice,
        'analysis_mode': 'ml',
    }


# ======= Cash Flow Analyzer =======
def analyze_cash_flow(csv_file=None, manual_data=None, lang='en'):
    """
    Input:
      - csv_file: path to CSV file (string) OR
      - manual_data: list of dict rows [{'month':..., 'fiscal year':..., 'inflows/outflows':..., 'amount':...}, ...]
    Returns:
      dict with keys: summary (list of records), insights (list), graph (base64 png), funding (dict), saved_file (path)
    """
    import traceback

    if csv_file:
        try:
            header = pd.read_csv(csv_file, nrows=0)
            upper_cols = {c.upper().strip() for c in header.columns}
            if {'FISCAL YEAR', 'MONTH', 'INFLOWS/OUTFLOWS', 'AMOUNT'}.issubset(upper_cols):
                use = [c for c in header.columns if c.upper().strip() in {
                    'FISCAL YEAR', 'MONTH', 'INFLOWS/OUTFLOWS', 'DESCRIPTION', 'AMOUNT',
                }]
                raw_df = pd.read_csv(csv_file, usecols=use, low_memory=False)
            else:
                raw_df = pd.read_csv(csv_file, low_memory=False)
        except Exception as e:
            raise ValueError(f'Error reading CSV file: {e}\n{traceback.format_exc()}')
    elif manual_data:
        raw_df = pd.DataFrame(manual_data)
    else:
        raise ValueError('Please upload a CSV or provide manual data.')

    monthly_summary = _build_monthly_summary(raw_df)
    lang = 'ar' if lang == 'ar' else 'en'
    insights = _build_insights(monthly_summary, lang=lang)
    graph_base64 = _build_net_cash_chart(monthly_summary)

    use_business = _should_use_business_model(raw_df, manual_data)
    if use_business:
        prediction = _business_forecast(monthly_summary)
        if prediction:
            prediction['forecast_chart'] = _build_outlook_chart(monthly_summary, prediction)
        else:
            prediction = {'warning': 'Not enough data for forecast.'}
    else:
        try:
            prediction = run_prediction_from_dataframe(raw_df)
            prediction['source'] = 'ml'
            if not _ml_forecast_reliable(prediction):
                business_pred = _business_forecast(monthly_summary)
                if business_pred:
                    prediction['forecast'] = business_pred['forecast']
                    prediction['forecast_chart'] = _build_outlook_chart(monthly_summary, business_pred)
                    prediction['source'] = 'business'
                    prediction['ml_note'] = 'unreliable'
            elif not prediction.get('forecast_chart'):
                prediction['forecast_chart'] = _build_outlook_chart(
                    monthly_summary,
                    {'forecast': prediction.get('forecast', {})},
                )
        except Exception as e:
            print('Cash flow prediction failed:', e)
            prediction = {'warning': str(e)}

    prediction_advice = _build_prediction_advice(prediction, monthly_summary, lang=lang)

    output_path = 'dataset/cash_flow_summary.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    monthly_summary['month'] = monthly_summary['month'].astype(str)
    monthly_summary['fiscal year'] = monthly_summary['fiscal year'].astype(str)
    monthly_summary.to_csv(output_path, index=False, encoding='utf-8-sig')

    return {
        'summary': monthly_summary.to_dict(orient='records'),
        'insights': insights,
        'graph': graph_base64,
        'prediction': prediction,
        'prediction_advice': prediction_advice,
        'saved_file': output_path,
    }
