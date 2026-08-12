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
    print("🔄 Training base regressors with CV (log1p target)...")
    
    for name, model in base_models:
        scores = []
        for train_idx, val_idx in kf.split(X_scaled):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y_log.iloc[train_idx], y_log.iloc[val_idx]
            model.fit(X_train, y_train)
            scores.append(model.score(X_val, y_val))
        print(f"✅ {name} CV R2 (log target): {np.mean(scores):.3f}")
    
    ensemble_model = VotingRegressor(estimators=base_models)
    ensemble_model.fit(X_scaled, y_log)
    print("💾 Ensemble trained on log1p(target).")
    
    # Domain scaling
    train_median = float(np.median(y))
    scale_factor = target_startup_median / (train_median + 1e-9)
    scale_info = {"train_median": train_median, "scale_factor": scale_factor, "target_startup_median": target_startup_median}
    
    os.makedirs("models", exist_ok=True)
    joblib.dump(ensemble_model, MODEL_FLOW_PATH)
    joblib.dump(scaler, SCALER_FLOW_PATH)
    joblib.dump(scale_info, SCALE_INFO_PATH)
    print(f"💾 Saved ensemble, scaler, scale info. Train median: {train_median:,.2f}, scale_factor: {scale_factor:.6f}")
    
    return ensemble_model, scaler, scale_info

# ==========================================
# Funding Analysis (uses predict_risk)
# ==========================================
def analyze_funding(funding, capital, revenue, expenses, growth_rate, duration, flow_model, scaler, scale_info):
    growth = float(growth_rate) / 100.0
    inflow = revenue * (1 + growth)
    outflow = expenses
    net_flow = inflow - outflow
    profitability = net_flow / (inflow + 1e-6)
    stability = 1 - abs(inflow - outflow) / (inflow + outflow + 1e-6)
    stability = float(max(0.0, min(1.0, stability)))
    
    predicted_risk = predict_risk(inflow, outflow, net_flow, profitability, stability)
    
    X_user = scaler.transform([[outflow, net_flow, profitability, stability]])
    y_log_pred = flow_model.predict(X_user)[0]
    y_pred_raw = float(np.expm1(y_log_pred))
    scaled_pred = y_pred_raw * float(scale_info.get("scale_factor", 1.0))
    scaled_pred = float(max(PREDICTION_CLIP_MIN, min(PREDICTION_CLIP_MAX, scaled_pred)))
    
    predicted_inflow = scaled_pred
    
    # Funding mix logic
    if predicted_risk == "low":
        equity, debt, grants = 20, 50, 30
    elif predicted_risk == "medium":
        equity, debt, grants = 15, 45, 40
    else:
        equity, debt, grants = 10, 35, 55
    
    # Adjust by funding/capital/profitability
    if funding < 100_000: equity, debt, grants = 5, 35, 60
    elif funding < 1_000_000: equity, debt, grants = 12, 43, 45
    else: equity, debt, grants = 25, 50, 25
    if capital < 250_000: grants += 10; equity -= 5
    elif capital < 500_000: grants += 5; equity -= 3
    if profitability > 0.5: debt -= 5; equity += 3
    elif profitability < 0.3: grants += 5; equity -= 2
    equity = max(equity, 3)
    
    total = equity + debt + grants
    equity, debt, grants = [round(x * 100 / total, 1) for x in (equity, debt, grants)]
    
    advice_dict = {
        "low": ("Low risk — use small equity with balanced debt financing.", 
                "AI suggests minimizing equity and leveraging stable debt sources."),
        "medium": ("Medium risk — grants and microfinance are key options.",
                   "AI recommends avoiding investor equity and focusing on government or NGO grants."),
        "high": ("High risk — prioritize grants and low-interest microloans.",
                 "AI suggests delaying equity rounds and protecting ownership.")
    }
    advice, ai_comment = advice_dict.get(predicted_risk, ("Unknown risk", ""))
    
    funding_mix = {"Equity": equity, "Debt": debt, "Grants": grants}
    
    return {
        "predicted_risk": predicted_risk,
        "profitability": profitability,
        "stability": stability,
        "equity": equity,
        "debt": debt,
        "grants": grants,
        "funding_mix": funding_mix,
        "advice": advice,
        "ai_comment": ai_comment,
        "predicted_inflow": predicted_inflow,
        "raw_public_inflow_estimate": y_pred_raw,
        "scale_info": scale_info
    }

# ==========================================
# Load or Train Models
# ==========================================
def train_models():
    if os.path.exists(MODEL_FLOW_PATH) and os.path.exists(SCALER_FLOW_PATH) and os.path.exists(SCALE_INFO_PATH):
        flow_model = joblib.load(MODEL_FLOW_PATH)
        scaler = joblib.load(SCALER_FLOW_PATH)
        scale_info = joblib.load(SCALE_INFO_PATH)
        print("✅ Loaded existing flow model, scaler, and scale info.")
        return flow_model, scaler, scale_info
    return train_flow_model(cv_folds=5, target_startup_median=TARGET_STARTUP_MEDIAN)

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    print("🚀 Training / Loading Flow Model...")
    flow_model, scaler, scale_info = train_models()
    print("✅ Flow model ready.\nScale info:", scale_info)
    
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
    
    print("\n💡 Funding Analysis Results:")
    for k, v in demo.items():
        print(f"{k}: {v}")
