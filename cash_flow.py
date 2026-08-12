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


def _build_insights(monthly_summary):
    insights = []
    for year in monthly_summary['fiscal year'].unique():
        data = monthly_summary[monthly_summary['fiscal year'] == year]
        avg_in = float(data['Total Inflows'].mean()) if 'Total Inflows' in data else 0.0
        avg_out = float(data['Total Outflows'].mean()) if 'Total Outflows' in data else 0.0
        avg_net = float(data['Net Cash Flow'].mean()) if 'Net Cash Flow' in data else 0.0

        try:
            best_row = data.loc[data['Net Cash Flow'].idxmax()]
            worst_row = data.loc[data['Net Cash Flow'].idxmin()]
            max_month = best_row['month']
            max_net = float(best_row['Net Cash Flow'])
            min_month = worst_row['month']
            min_net = float(worst_row['Net Cash Flow'])
        except Exception:
            max_month = None
            max_net = 0.0
            min_month = None
            min_net = 0.0

        trend = 'positive' if avg_net > 0 else 'negative'
        insights.append({
            'year': str(year),
            'avg_inflow': round(avg_in, 2),
            'avg_outflow': round(avg_out, 2),
            'avg_net': round(avg_net, 2),
            'trend': trend,
            'max_month': max_month,
            'max_net': round(max_net, 2),
            'min_month': min_month,
            'min_net': round(min_net, 2),
            'advice': 'Healthy financials.' if trend == 'positive' else 'Caution: control spending.',
        })
    return insights


def _build_net_cash_chart(monthly_summary):
    plt.figure(figsize=(10, 5))
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
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    graph_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return graph_base64


def _build_prediction_advice(prediction):
    """Derive business advice from ending-balance forecast."""
    if not prediction or prediction.get('warning'):
        return None

    forecast = prediction.get('forecast', {})
    change = forecast.get('change', 0)
    trend = forecast.get('trend', 'down')
    next_balance = forecast.get('next_ending_balance', 0)
    last_balance = forecast.get('last_ending_balance', 0)

    if trend == 'up' and change > 0:
        risk_level = 'LOW'
        advice = 'Ending balance is projected to rise — maintain current cash management.'
    elif abs(change) < max(abs(last_balance) * 0.05, 1):
        risk_level = 'MEDIUM'
        advice = 'Ending balance is stable — monitor inflows and outflows closely.'
    else:
        risk_level = 'HIGH'
        advice = 'Ending balance may decline — reduce costs and improve collections.'

    return {
        'next_ending_balance': next_balance,
        'last_ending_balance': last_balance,
        'change': change,
        'trend': trend,
        'best_model': prediction.get('best_model'),
        'risk_level': risk_level,
        'advice': advice,
    }


# ======= Cash Flow Analyzer =======
def analyze_cash_flow(csv_file=None, manual_data=None):
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
            raw_df = pd.read_csv(csv_file)
        except Exception as e:
            raise ValueError(f'Error reading CSV file: {e}\n{traceback.format_exc()}')
    elif manual_data:
        raw_df = pd.DataFrame(manual_data)
    else:
        raise ValueError('Please upload a CSV or provide manual data.')

    monthly_summary = _build_monthly_summary(raw_df)
    insights = _build_insights(monthly_summary)
    graph_base64 = _build_net_cash_chart(monthly_summary)

    try:
        prediction = run_prediction_from_dataframe(raw_df)
    except Exception as e:
        print('Cash flow prediction failed:', e)
        prediction = {'warning': str(e)}

    prediction_advice = _build_prediction_advice(prediction)

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
