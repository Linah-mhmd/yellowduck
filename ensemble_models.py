# ==========================================
# ensemble_models.py
# Ensemble + Meta-DES for Risk Classification
# ==========================================

import os
import joblib
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from deslib.des import METADES
from sklearn.metrics import accuracy_score, f1_score, classification_report

warnings.filterwarnings("ignore")

MODEL_SAVE_PATH = "models/ensemble_model.pkl"
SCALER_SAVE_PATH = "models/scaler.pkl"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"

# ==========================================
# Load & Prepare Dataset
# ==========================================
def load_and_prepare_data(csv_path="dataset/Financial_Plan_Statements_-_Cash_Flow.csv"):
    df = pd.read_csv(csv_path, on_bad_lines='skip', encoding="utf-8-sig")
    df["AMOUNT"] = df["AMOUNT"].astype(str).str.replace(",", "").str.replace("(", "-").str.replace(")", "")
    df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce").fillna(0.0)
    
    df["INFLOWS/OUTFLOWS"] = df["INFLOWS/OUTFLOWS"].astype(str).str.lower()
    df["type"] = df["INFLOWS/OUTFLOWS"].apply(lambda x: "inflow" if "inflow" in x else ("outflow" if "outflow" in x else "unknown"))
    
    grouped = df.groupby(["FISCAL YEAR", "MONTH", "type"])["AMOUNT"].sum().unstack().fillna(0)
    grouped["net_flow"] = grouped.get("inflow", 0) - grouped.get("outflow", 0)
    grouped["profitability"] = grouped["net_flow"] / (grouped.get("inflow", 0) + 1e-6)
    grouped["stability"] = 1 - (grouped["net_flow"].rolling(3, min_periods=1).std().fillna(0) / (abs(grouped["net_flow"]) + 1e-6))
    grouped["stability"] = grouped["stability"].clip(0, 1)
    
    grouped["risk_score"] = 0.5*(1 - grouped["profitability"].clip(0,1)) + 0.5*(1 - grouped["stability"])
    grouped["risk_level"] = pd.cut(grouped["risk_score"], bins=[0,0.33,0.66,1], labels=["low","medium","high"])
    
    features = ["inflow","outflow","net_flow","profitability","stability"]
    grouped = grouped.reset_index(drop=True)
    X = grouped[features].fillna(0)
    y = grouped["risk_level"].fillna("medium")
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    return X, y_encoded, le

# ==========================================
# Train Ensemble + Meta-DES
# ==========================================
def train_ensemble_model(n_splits=5):
    print("Loading & preprocessing dataset...")
    X, y, le = load_and_prepare_data()
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    os.makedirs("models", exist_ok=True)
    
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    accuracies, f1_scores = [], []
    
    for fold, (train_idx, test_idx) in enumerate(skf.split(X_scaled, y), 1):
        print(f"\nFold {fold}/{n_splits}")
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        base_models = [
            XGBClassifier(use_label_encoder=False, eval_metric="mlogloss", objective="multi:softmax",
                          num_class=len(np.unique(y)), max_depth=3, learning_rate=0.1, n_estimators=50, reg_lambda=1),
            LGBMClassifier(max_depth=3, learning_rate=0.1, n_estimators=50, reg_lambda=1),
            RandomForestClassifier(n_estimators=100, max_depth=4),
            GradientBoostingClassifier(n_estimators=50, max_depth=3),
            SVC(probability=True, C=1.0, kernel="rbf")
        ]
        
        for model in base_models: model.fit(X_train, y_train)
        meta_des = METADES(pool_classifiers=base_models)
        meta_des.fit(X_train, y_train)
        
        y_pred = meta_des.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")
        accuracies.append(acc)
        f1_scores.append(f1)
        print("Accuracy:", acc, "F1:", f1)
        print(classification_report(y_test, y_pred))
    
    print("\nCV Mean Accuracy:", np.mean(accuracies), "Mean F1:", np.mean(f1_scores))
    
    # Train final model on all data
    final_base_models = [
        XGBClassifier(use_label_encoder=False, eval_metric="mlogloss", objective="multi:softmax",
                      num_class=len(np.unique(y)), max_depth=3, learning_rate=0.1, n_estimators=50, reg_lambda=1),
        LGBMClassifier(max_depth=3, learning_rate=0.1, n_estimators=50, reg_lambda=1),
        RandomForestClassifier(n_estimators=100, max_depth=4),
        GradientBoostingClassifier(n_estimators=50, max_depth=3),
        SVC(probability=True, C=1.0, kernel="rbf")
    ]
    for model in final_base_models: model.fit(X_scaled, y)
    final_meta_des = METADES(pool_classifiers=final_base_models)
    final_meta_des.fit(X_scaled, y)
    
    joblib.dump(final_meta_des, MODEL_SAVE_PATH)
    joblib.dump(scaler, SCALER_SAVE_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    print("\nFinal Model, Scaler & LabelEncoder saved successfully!")
    
    return final_meta_des, scaler, le

# ==========================================
# Prediction Function (cached in memory)
# ==========================================
_risk_models = None


def get_risk_models():
    global _risk_models
    if _risk_models is None:
        if not all(os.path.exists(p) for p in (MODEL_SAVE_PATH, SCALER_SAVE_PATH, LABEL_ENCODER_PATH)):
            train_ensemble_model()
        _risk_models = (
            joblib.load(MODEL_SAVE_PATH),
            joblib.load(SCALER_SAVE_PATH),
            joblib.load(LABEL_ENCODER_PATH),
        )
    return _risk_models


def predict_risk(inflow, outflow, net_flow, profitability, stability):
    model, scaler, le = get_risk_models()
    X_sample = scaler.transform([[inflow, outflow, net_flow, profitability, stability]])
    pred = model.predict(X_sample)[0]
    return le.inverse_transform([pred])[0]

# ==========================================
if __name__ == "__main__":
    print("Training Ensemble Meta-DES Model...")
    train_ensemble_model()
    print("Training Completed Successfully!")
