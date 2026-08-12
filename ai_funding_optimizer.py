# ==========================================
# ai_funding_optimizer.py

# ==========================================

import os
import joblib
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from ensemble_models import predict_risk  # Meta-DES for risk (trained separately)

warnings.filterwarnings("ignore")

MODEL_FLOW_PATH = "models/ensemble_flow_model.pkl"
SCALER_FLOW_PATH = "models/scaler_flow.pkl"
SCALE_INFO_PATH = "models/flow_scale_info.pkl"

# ----------------------------
# Configurable parameters
# ----------------------------
TARGET_STARTUP_MEDIAN = 100_000
PREDICTION_CLIP_MIN = 1_000
PREDICTION_CLIP_MAX = 1_000_000

# ==========================================
# Load & Prepare Raw Flow Data
# ==========================================
def load_flow_data(csv_path="dataset/Financial_Plan_Statements_-_Cash_Flow.csv"):
    """Loads CSV and returns aggregated dataframe with derived metrics."""
    df = pd.read_csv(csv_path, on_bad_lines='skip', encoding="utf-8-sig")
    
    # Clean numeric AMOUNT column
    df["AMOUNT"] = df["AMOUNT"].astype(str).str.replace(",", "").str.replace("(", "-").str.replace(")", "")
    df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce").fillna(0.0)
    
    # Standardize inflows/outflows
    df["INFLOWS/OUTFLOWS"] = df["INFLOWS/OUTFLOWS"].astype(str).str.lower()
    df["type"] = df["INFLOWS/OUTFLOWS"].apply(lambda x: "inflow" if "inflow" in x else ("outflow" if "outflow" in x else "unknown"))
    
    grouped = df.groupby(["FISCAL YEAR", "MONTH", "type"])["AMOUNT"].sum().unstack().fillna(0)
    grouped["net_flow"] = grouped.get("inflow", 0) - grouped.get("outflow", 0)
    
    # Derived metrics
    grouped["profitability"] = grouped["net_flow"] / (grouped.get("inflow", 0) + 1e-6)
    grouped["stability"] = 1 - (grouped["net_flow"].rolling(3, min_periods=1).std().fillna(0) / (abs(grouped["net_flow"]) + 1e-6))
    grouped["stability"] = grouped["stability"].clip(0, 1)
    
    grouped = grouped.reset_index(drop=True)
    return grouped

# ==========================================
# Train Flow Model (Ensemble)
# ==========================================
def train_flow_model(cv_folds=5, target_startup_median=TARGET_STARTUP_MEDIAN):
    """Trains ensemble on log1p(inflow), computes domain scaling, saves models & scaler."""
    grouped = load_flow_data()
    
    # Optional augmentation for better distribution
    aug = []
    for _ in range(3000):
        inflow = np.random.uniform(20_000, 2_000_000)
        outflow = np.random.uniform(10_000, inflow)
        net = inflow - outflow
        profitability = net / inflow
        stability = np.random.uniform(0.3, 1.0)
        aug.append([inflow, outflow, net, profitability, stability])
    aug_df = pd.DataFrame(aug, columns=["inflow", "outflow", "net_flow", "profitability", "stability"])
    grouped = pd.concat([grouped, aug_df], ignore_index=True)
    
    features = ["outflow", "net_flow", "profitability", "stability"]
    X = grouped[features].fillna(0)
    y = grouped["inflow"].fillna(grouped["inflow"].mean())
    y_log = np.log1p(y)  # log1p transform
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Base regressors
    base_models = [
        ("xgb", XGBRegressor(max_depth=3, learning_rate=0.05, n_estimators=150, reg_lambda=1.0, reg_alpha=0.5, random_state=42, verbosity=0)),
        ("lgbm", LGBMRegressor(max_depth=3, learning_rate=0.05, n_estimators=150, min_data_in_leaf=10, reg_lambda=1.0, reg_alpha=0.5, random_state=42)),
        ("rf", RandomForestRegressor(max_depth=4, n_estimators=150, min_samples_leaf=5, random_state=42)),
        ("gbr", GradientBoostingRegressor(max_depth=3, n_estimators=150, learning_rate=0.05, random_state=42)),
        ("svr", SVR(C=1.0, kernel="rbf", epsilon=0.01))
    ]
    
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    print("Training base regressors with CV (log1p target)...")
    
    for name, model in base_models:
        scores = []
        for train_idx, val_idx in kf.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y_log.iloc[train_idx], y_log.iloc[val_idx]
            model.fit(X_train, y_train)
            scores.append(model.score(X_val, y_val))
        print(f"[OK] {name} CV R2 (log target): {np.mean(scores):.3f}")
    
    ensemble_model = VotingRegressor(estimators=base_models)
    ensemble_model.fit(X_scaled, y_log)
    print("Ensemble trained on log1p(target).")
    
    # Domain scaling
    train_median = float(np.median(y))
    scale_factor = target_startup_median / (train_median + 1e-9)
    scale_info = {"train_median": train_median, "scale_factor": scale_factor, "target_startup_median": target_startup_median}
    
    os.makedirs("models", exist_ok=True)
    joblib.dump(ensemble_model, MODEL_FLOW_PATH)
    joblib.dump(scaler, SCALER_FLOW_PATH)
    joblib.dump(scale_info, SCALE_INFO_PATH)
    print(f"Saved ensemble, scaler, scale info. Train median: {train_median:,.2f}, scale_factor: {scale_factor:.6f}")
    
    return ensemble_model, scaler, scale_info

# ==========================================
# Funding Analysis (uses predict_risk + business metrics)
# ==========================================

def _compute_business_metrics(funding, capital, revenue, expenses, growth_rate, duration):
    """Derive founder-friendly metrics directly from inputs."""
    annual_growth = float(growth_rate) / 100.0
    duration = max(1, int(duration))
    funding = float(funding)
    capital = float(capital)
    revenue = float(revenue)
    expenses = float(expenses)

    monthly_growth = (1 + annual_growth) ** (1 / 12) - 1 if annual_growth > 0 else 0.0
    projected_monthly_revenue = revenue * (1 + monthly_growth)
    monthly_net = projected_monthly_revenue - expenses
    monthly_burn = max(0.0, -monthly_net)
    profitability = monthly_net / (projected_monthly_revenue + 1e-6)

    if monthly_burn > 0:
        runway_months = capital / monthly_burn
    else:
        runway_months = None

    total_revenue = sum(revenue * ((1 + monthly_growth) ** m) for m in range(duration))
    total_expenses = expenses * duration
    net_over_duration = total_revenue - total_expenses
    cumulative_shortfall = max(0.0, -net_over_duration)
    external_need = max(0.0, cumulative_shortfall - capital)

    if external_need > 0:
        funding_coverage_pct = round((funding / external_need) * 100, 1)
        funding_surplus = round(max(0.0, funding - external_need), 2)
        funding_gap = round(max(0.0, external_need - funding), 2)
    else:
        funding_coverage_pct = None
        funding_surplus = round(max(0.0, funding), 2) if funding > 0 else 0.0
        funding_gap = 0.0

    break_even_revenue = expenses / (1 + monthly_growth) if (1 + monthly_growth) > 0 else expenses
    revenue_gap_to_break_even = max(0.0, break_even_revenue - revenue)

    if monthly_burn == 0 and monthly_net >= 0:
        health = 'growth'
    elif runway_months is not None and runway_months < 3:
        health = 'critical'
    elif runway_months is not None and (runway_months < duration or monthly_net < 0):
        health = 'caution'
    else:
        health = 'stable'

    return {
        'projected_monthly_revenue': round(projected_monthly_revenue, 2),
        'monthly_net': round(monthly_net, 2),
        'monthly_burn': round(monthly_burn, 2),
        'profitability': round(profitability, 4),
        'runway_months': round(runway_months, 1) if runway_months is not None else None,
        'break_even_revenue': round(break_even_revenue, 2),
        'revenue_gap_to_break_even': round(revenue_gap_to_break_even, 2),
        'cumulative_shortfall': round(cumulative_shortfall, 2),
        'external_need': round(external_need, 2),
        'funding_coverage_pct': funding_coverage_pct,
        'funding_surplus': funding_surplus,
        'funding_gap': funding_gap,
        'net_over_duration': round(net_over_duration, 2),
        'health': health,
        'duration': duration,
        'annual_growth_pct': round(annual_growth * 100, 2),
    }


def _runway_alert(metrics, lang='en'):
    runway = metrics['runway_months']
    duration = metrics['duration']
    if runway is None or metrics['monthly_burn'] <= 0 or runway >= duration:
        return None
    month = max(1, int(np.ceil(runway)))
    if lang == 'ar':
        return {
            'funding_needed_by_month': month,
            'message': (
                f'تحتاجين تمويلاً قبل الشهر {month} '
                f'(المدى {runway:.1f} شهر مقابل {duration} شهر للمشروع).'
            ),
        }
    return {
        'funding_needed_by_month': month,
        'message': (
            f'You need funding before month {month} '
            f'(runway {runway:.1f} months vs {duration}-month project).'
        ),
    }


def _compute_scenarios(funding, capital, revenue, expenses, growth_rate, duration):
    base = _compute_business_metrics(funding, capital, revenue, expenses, growth_rate, duration)
    configs = [
        ('reduce_expenses_10', expenses * 0.9, revenue),
        ('increase_revenue_20', expenses, revenue * 1.2),
    ]
    scenarios = []
    for scenario_id, scen_expenses, scen_revenue in configs:
        m = _compute_business_metrics(funding, capital, scen_revenue, scen_expenses, growth_rate, duration)
        scenarios.append({
            'id': scenario_id,
            'monthly_burn': m['monthly_burn'],
            'runway_months': m['runway_months'],
            'external_need': m['external_need'],
            'health': m['health'],
            'burn_change': round(m['monthly_burn'] - base['monthly_burn'], 2),
            'external_need_change': round(m['external_need'] - base['external_need'], 2),
        })
    return scenarios


STAGE_MIX_ADJUST = {
    'idea': {'equity': -8, 'debt': -7, 'grants': 15},
    'seed': {'equity': 0, 'debt': 0, 'grants': 0},
    'growth': {'equity': 12, 'debt': 8, 'grants': -20},
}


def _adjust_risk_level(ml_risk, metrics):
    """Blend ML risk with business signals."""
    risk_rank = {'low': 0, 'medium': 1, 'high': 2}
    rank = risk_rank.get(str(ml_risk).lower(), 1)

    if metrics['monthly_burn'] > 0 and metrics['runway_months'] is not None:
        if metrics['runway_months'] < 3:
            rank = max(rank, 2)
        elif metrics['runway_months'] < metrics['duration']:
            rank = max(rank, 1)

    if metrics['profitability'] < -0.25:
        rank = max(rank, 2)
    elif metrics['profitability'] > 0.25 and metrics['monthly_burn'] == 0:
        rank = min(rank, 0)

    if metrics['funding_coverage_pct'] is not None and metrics['funding_coverage_pct'] < 60:
        rank = max(rank, 1)

    return ('low', 'medium', 'high')[rank]


def _recommend_funding_mix(risk, metrics, funding, stage='seed'):
    equity, debt, grants = {'low': (22, 48, 30), 'medium': (12, 38, 50), 'high': (6, 28, 66)}[risk]
    stage = str(stage or 'seed').lower()
    if stage not in STAGE_MIX_ADJUST:
        stage = 'seed'
    adj = STAGE_MIX_ADJUST[stage]
    equity += adj['equity']
    debt += adj['debt']
    grants += adj['grants']

    if metrics['profitability'] < 0:
        grants += 12
        equity -= 8
    elif metrics['profitability'] > 0.2:
        debt += 8
        grants -= 5

    if metrics['monthly_burn'] > 0:
        if metrics['runway_months'] is not None and metrics['runway_months'] < metrics['duration']:
            grants += 8
            equity -= 5
        if metrics['runway_months'] is not None and metrics['runway_months'] < 6:
            grants += 5
            debt -= 5

    if funding < 100_000:
        grants += 8
        equity -= 4
    elif funding > 1_000_000:
        equity += 10
        grants -= 8

    if metrics['external_need'] > 0 and metrics['funding_coverage_pct'] is not None and metrics['funding_coverage_pct'] < 75:
        grants += 5
        debt -= 3

    if risk == 'high' and metrics['profitability'] < 0:
        debt -= 12
        grants += 12

    equity = max(equity, 2)
    debt = max(debt, 0)
    grants = max(grants, 10)
    if risk == 'high' and metrics['profitability'] < 0:
        debt = min(debt, 10)
    total = equity + debt + grants
    return [round(x * 100 / total, 1) for x in (equity, debt, grants)]


def _explain_risk(ml_risk, predicted_risk, metrics, stability, lang='en'):
    factors = []
    runway = metrics['runway_months']
    duration = metrics['duration']

    if lang == 'ar':
        if metrics['monthly_burn'] > 0:
            factors.append('المصروفات الشهرية أعلى من الإيرادات المتوقعة (بعد النمو السنوي).')
        if runway is not None and runway < duration:
            factors.append(f'المدى الزمني ({runway:.1f} شهر) أقصر من مدة المشروع ({duration} شهر).')
        if metrics['profitability'] < 0:
            factors.append('الربحية الشهرية سالبة — الشركة تحرق cash.')
        if stability >= 0.75 and predicted_risk == 'high':
            factors.append('الاستقرار مرتفع: المخاطرة بسبب المدى الزمني وليس انهياراً مالياً.')
    else:
        if metrics['monthly_burn'] > 0:
            factors.append('Monthly expenses exceed projected revenue (after annual growth).')
        if runway is not None and runway < duration:
            factors.append(f'Runway ({runway:.1f} mo) is shorter than project duration ({duration} mo).')
        if metrics['profitability'] < 0:
            factors.append('Monthly profitability is negative — the company is burning cash.')
        if stability >= 0.75 and predicted_risk == 'high':
            factors.append('Stability is high: risk is driven by runway, not a financial collapse.')
    return factors


def _scenario_tip(scenarios, lang='en'):
    if not scenarios:
        return None
    best = min(scenarios, key=lambda s: s.get('external_need', 0))
    if best['id'] == 'increase_revenue_20':
        if lang == 'ar':
            return 'أفضل خيار: زيادة الإيراد 20% — يلغي أو يقلّل الاحتياج الخارجي.'
        return 'Best scenario (+20% revenue): eliminates or greatly reduces external need.'
    if best['id'] == 'reduce_expenses_10':
        if lang == 'ar':
            return 'أفضل خيار: خفض المصروفات 10% — يقلّل الحرق والاحتياج الخارجي.'
        return 'Best scenario (-10% expenses): lowers burn and external need.'
    return None


def _build_advice_points(metrics, funding, equity, debt, grants, predicted_risk, stage='seed', use_of_funds='', scenarios=None, lang='en'):
    """Bullet-point insights tailored to the business."""
    points = []
    runway = metrics['runway_months']
    duration = metrics['duration']
    burn = metrics['monthly_burn']
    stage = str(stage or 'seed').lower()
    funds_text = (use_of_funds or '').strip()

    if lang == 'ar':
        stage_labels = {'idea': 'فكرة', 'seed': 'بذرة', 'growth': 'نمو'}
        points.append(f'مرحلة الشركة: {stage_labels.get(stage, stage)}.')
        if funds_text:
            points.append(f'استخدام التمويل: {funds_text}')
        else:
            points.append('أضيفي "استخدام التمويل" في النموذج لربط المبلغ بخطة أوضح.')
        health_msgs = {
            'critical': 'وضع حرج: رأس المال يغطي أقل من 3 أشهر.',
            'caution': 'تحذير: مصروفات > إيرادات أو المدى الزمني أقصر من مدة المشروع.',
            'stable': 'وضع مستقر نسبياً على مدة المشروع.',
            'growth': 'تدفق نقدي إيجابي — التوسع ممكن من الإيرادات.',
        }
        points.append(health_msgs.get(metrics['health'], ''))
        if burn > 0 and runway is not None:
            points.append(f'المدى الزمني: {runway:.1f} من {duration} شهر.')
        if metrics['revenue_gap_to_break_even'] > 0:
            points.append(
                f'للتعادل: ≈ {metrics["break_even_revenue"]:,.0f} إيراد شهري '
                f'(فجوة {metrics["revenue_gap_to_break_even"]:,.0f}).'
            )
        if metrics['external_need'] > 0:
            if metrics['funding_gap'] > 0:
                points.append(
                    f'طلب التمويل أقل من الاحتياج بـ {metrics["funding_gap"]:,.0f}.'
                )
            else:
                points.append(
                    f'الطلب يغطي {metrics["funding_coverage_pct"]:.0f}% من الاحتياج ({metrics["external_need"]:,.0f}).'
                )
                if metrics['funding_surplus'] > 0:
                    points.append(f'فائض تقديري: {metrics["funding_surplus"]:,.0f}.')
        points.append(f'مزيج مقترح: منح {grants}% · ديون {debt}% · أسهم {equity}%.')
        if predicted_risk == 'high' and debt > 5:
            points.append('الديون التقليدية صعبة — ركّزي على منح وقروض مبرمجة/منخفضة الفائدة.')
    else:
        stage_labels = {'idea': 'Idea', 'seed': 'Seed', 'growth': 'Growth'}
        points.append(f'Company stage: {stage_labels.get(stage, stage)}.')
        if funds_text:
            points.append(f'Use of funds: {funds_text}')
        else:
            points.append('Add "Use of funds" in the form to tie the amount to a clearer plan.')
        health_msgs = {
            'critical': 'Critical: capital covers less than 3 months.',
            'caution': 'Caution: expenses > revenue or runway shorter than project duration.',
            'stable': 'Relatively stable for the project timeline.',
            'growth': 'Positive cash flow — growth can be funded from revenue.',
        }
        points.append(health_msgs.get(metrics['health'], ''))
        if burn > 0 and runway is not None:
            points.append(f'Runway: {runway:.1f} of {duration} months.')
        if metrics['revenue_gap_to_break_even'] > 0:
            points.append(
                f'Break-even: ≈ {metrics["break_even_revenue"]:,.0f}/month '
                f'(gap {metrics["revenue_gap_to_break_even"]:,.0f}).'
            )
        if metrics['external_need'] > 0:
            if metrics['funding_gap'] > 0:
                points.append(f'Funding request is below need by {metrics["funding_gap"]:,.0f}.')
            else:
                points.append(
                    f'Request covers {metrics["funding_coverage_pct"]:.0f}% of need ({metrics["external_need"]:,.0f}).'
                )
                if metrics['funding_surplus'] > 0:
                    points.append(f'Estimated surplus: {metrics["funding_surplus"]:,.0f}.')
        points.append(f'Suggested mix: grants {grants}% · debt {debt}% · equity {equity}%.')
        if predicted_risk == 'high' and debt > 5:
            points.append('Traditional bank debt may be difficult — prioritize grants and subsidized loans.')

    tip = _scenario_tip(scenarios, lang)
    if tip:
        points.append(tip)

    return [p for p in points if p]


def analyze_funding(
    funding, capital, revenue, expenses, growth_rate, duration,
    flow_model, scaler, scale_info,
    stage='seed', use_of_funds='', lang='en',
):
    stage = str(stage or 'seed').lower()
    if stage not in STAGE_MIX_ADJUST:
        stage = 'seed'

    metrics = _compute_business_metrics(funding, capital, revenue, expenses, growth_rate, duration)
    runway_alert = _runway_alert(metrics, lang)
    scenarios = _compute_scenarios(funding, capital, revenue, expenses, growth_rate, duration)

    inflow = metrics['projected_monthly_revenue']
    outflow = float(expenses)
    net_flow = metrics['monthly_net']
    profitability = metrics['profitability']
    stability = 1 - abs(inflow - outflow) / (inflow + outflow + 1e-6)
    stability = float(max(0.0, min(1.0, stability)))

    ml_risk = predict_risk(inflow, outflow, net_flow, profitability, stability)
    predicted_risk = _adjust_risk_level(ml_risk, metrics)

    equity, debt, grants = _recommend_funding_mix(predicted_risk, metrics, float(funding), stage)
    risk_factors = _explain_risk(ml_risk, predicted_risk, metrics, stability, lang)
    advice_points = _build_advice_points(
        metrics, float(funding), equity, debt, grants, predicted_risk,
        stage, use_of_funds, scenarios, lang,
    )
    advice = ' '.join(advice_points)

    # ML benchmark kept for internal reference only — not shown as primary revenue forecast
    X_user = scaler.transform([[outflow, net_flow, profitability, stability]])
    y_log_pred = flow_model.predict(X_user)[0]
    y_pred_raw = float(np.expm1(y_log_pred))
    ml_benchmark = float(max(PREDICTION_CLIP_MIN, min(PREDICTION_CLIP_MAX, y_pred_raw * float(scale_info.get('scale_factor', 1.0)))))

    return {
        'predicted_risk': predicted_risk,
        'ml_risk': ml_risk,
        'profitability': profitability,
        'stability': stability,
        'equity': equity,
        'debt': debt,
        'grants': grants,
        'funding_mix': {'Equity': equity, 'Debt': debt, 'Grants': grants},
        'advice': advice,
        'advice_points': advice_points,
        'risk_factors': risk_factors,
        'health': metrics['health'],
        'projected_monthly_revenue': metrics['projected_monthly_revenue'],
        'monthly_burn': metrics['monthly_burn'],
        'monthly_net': metrics['monthly_net'],
        'runway_months': metrics['runway_months'],
        'break_even_revenue': metrics['break_even_revenue'],
        'revenue_gap_to_break_even': metrics['revenue_gap_to_break_even'],
        'external_need': metrics['external_need'],
        'funding_coverage_pct': metrics['funding_coverage_pct'],
        'funding_surplus': metrics['funding_surplus'],
        'funding_gap': metrics['funding_gap'],
        'net_over_duration': metrics['net_over_duration'],
        'stage': stage,
        'use_of_funds': use_of_funds.strip() if use_of_funds else '',
        'runway_alert': runway_alert,
        'scenarios': scenarios,
        'ml_inflow_benchmark': ml_benchmark,
        # backward compatibility
        'predicted_inflow': metrics['projected_monthly_revenue'],
    }

# ==========================================
# Load or Train Models
# ==========================================
def train_models():
    if os.path.exists(MODEL_FLOW_PATH) and os.path.exists(SCALER_FLOW_PATH) and os.path.exists(SCALE_INFO_PATH):
        flow_model = joblib.load(MODEL_FLOW_PATH)
        scaler = joblib.load(SCALER_FLOW_PATH)
        scale_info = joblib.load(SCALE_INFO_PATH)
        print("Loaded existing flow model, scaler, and scale info.")
        return flow_model, scaler, scale_info
    return train_flow_model(cv_folds=5, target_startup_median=TARGET_STARTUP_MEDIAN)

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    print("Training / Loading Flow Model...")
    flow_model, scaler, scale_info = train_models()
    print("Flow model ready.\nScale info:", scale_info)
    
    demo = analyze_funding(
        funding=500_000,
        capital=300_000,
        revenue=450_000,
        expenses=200_000,
        growth_rate=0.1,
        duration=12,
        flow_model=flow_model,
        scaler=scaler,
        scale_info=scale_info
    )
    
    print("\nFunding Analysis Results:")
    for k, v in demo.items():
        print(f"{k}: {v}")
