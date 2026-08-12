"""Cash Flow Ending Balance prediction — LMX + MetaDES ensemble."""
import io
import base64
import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler, KBinsDiscretizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor, KNeighborsClassifier
from sklearn.linear_model import Ridge

matplotlib.use('Agg')
warnings.filterwarnings('ignore')

DEFAULT_DATASET = os.path.join(
    os.path.dirname(__file__), 'dataset', 'Financial_Plan_Statements_-_Cash_Flow.csv'
)

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
}


def _evaluate(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    r2 = r2_score(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(mean_absolute_percentage_error(y_true, y_pred) * 100)
    return round(r2, 4), round(rmse, 2), round(mape, 2)


def _get_oof_predictions(model, X, y, tscv):
    oof = np.zeros(len(X))
    for train_idx, val_idx in tscv.split(X):
        m = clone(model)
        m.fit(X[train_idx], y.iloc[train_idx].values)
        oof[val_idx] = m.predict(X[val_idx])
    return oof


def _chart_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data


def _is_official_format(df):
    cols = {c.upper().strip() for c in df.columns}
    return {'FISCAL YEAR', 'MONTH', 'INFLOWS/OUTFLOWS', 'DESCRIPTION', 'AMOUNT'}.issubset(cols)


def _normalize_official_df(df):
    df = df.copy()
    # Official file may contain duplicate lowercase columns — keep uppercase set only
    upper_map = {}
    for col in df.columns:
        key = col.upper().strip()
        if key not in upper_map:
            upper_map[key] = col
    df = df[[upper_map[k] for k in upper_map]].copy()
    df.columns = [c.upper().strip() for c in df.columns]

    amount_col = df['AMOUNT']
    if isinstance(amount_col, pd.DataFrame):
        amount_col = amount_col.iloc[:, 0]
    df['AMOUNT'] = pd.to_numeric(amount_col, errors='coerce').fillna(0)
    df['FISCAL YEAR'] = pd.to_numeric(df['FISCAL YEAR'], errors='coerce')
    if 'PUBLICATION DATE' in df.columns:
        df['PUBLICATION DATE'] = pd.to_datetime(df['PUBLICATION DATE'], format='%Y%m%d', errors='coerce')
    df['MONTH_num'] = df['MONTH'].astype(str).str.strip().str.title().map(
        {k.title(): v for k, v in MONTH_MAP.items()}
    )
    sort_cols = ['FISCAL YEAR', 'PUBLICATION DATE'] if 'PUBLICATION DATE' in df.columns else ['FISCAL YEAR']
    df = df.sort_values(sort_cols)
    df['MONTH_num'] = df['MONTH_num'].ffill()
    df = df.dropna(subset=['MONTH_num', 'FISCAL YEAR'])
    df['DATE'] = pd.to_datetime(
        df['FISCAL YEAR'].astype(int).astype(str) + '-' + df['MONTH_num'].astype(int).astype(str) + '-01'
    )
    pivot_df = df.pivot_table(
        index=['DATE', 'FISCAL YEAR', 'MONTH_num'],
        columns=['INFLOWS/OUTFLOWS', 'DESCRIPTION'],
        values='AMOUNT',
        aggfunc='sum',
    ).fillna(0)
    pivot_df.columns = ['_'.join(map(str, col)).strip() for col in pivot_df.columns.values]
    return pivot_df.reset_index()


def _normalize_simple_df(df):
    """Convert simplified app CSV/manual rows to monthly ending balance series."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    required = ['month', 'fiscal year', 'inflows/outflows', 'amount']
    for col in required:
        if col not in df.columns:
            raise ValueError(f'Missing required column: {col}')

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    df['month'] = df['month'].astype(str).str.strip().str.title()
    df['fiscal year'] = df['fiscal year'].astype(str).str.strip()
    df['inflows/outflows'] = df['inflows/outflows'].astype(str).str.strip().str.title()

    monthly = df.groupby(['fiscal year', 'month', 'inflows/outflows'])['amount'].sum().unstack(fill_value=0)
    monthly['Total Inflows'] = monthly.filter(regex='(?i)inflow').sum(axis=1)
    monthly['Total Outflows'] = monthly.filter(regex='(?i)outflow').sum(axis=1)
    monthly['Net_Cash_Flow'] = monthly['Total Inflows'] - monthly['Total Outflows']
    monthly = monthly.reset_index()

    month_order = [m.title() for m in MONTH_MAP.keys()]
    monthly['MONTH_num'] = monthly['month'].map({m: i + 1 for i, m in enumerate(month_order)})
    monthly['FISCAL YEAR'] = pd.to_numeric(monthly['fiscal year'], errors='coerce')
    monthly['DATE'] = pd.to_datetime(
        monthly['FISCAL YEAR'].astype(int).astype(str) + '-' + monthly['MONTH_num'].astype(int).astype(str) + '-01'
    )
    monthly = monthly.sort_values('DATE').reset_index(drop=True)
    monthly['Balance_Ending Balance'] = monthly['Net_Cash_Flow'].cumsum()

    pivot_df = monthly[['DATE', 'FISCAL YEAR', 'MONTH_num', 'Total Inflows', 'Total Outflows', 'Net_Cash_Flow', 'Balance_Ending Balance']].copy()
    pivot_df = pivot_df.rename(columns={
        'Total Inflows': 'Inflows - Current_Total',
        'Total Outflows': 'Outflows - Current_Total',
    })
    return pivot_df


def _engineer_features(pivot_df):
    target_cols = [c for c in pivot_df.columns if 'Ending Balance' in c]
    if not target_cols:
        raise ValueError('Could not find Ending Balance column in cash flow data.')
    target_col = target_cols[0]
    y = pivot_df[target_col].copy()

    exclude = ['DATE', 'FISCAL YEAR', 'MONTH_num', target_col, 'Balance_Beginning Balance']
    feature_cols = [c for c in pivot_df.columns if c not in exclude]
    X = pivot_df[feature_cols].copy()

    inflow_cols = [c for c in X.columns if 'Inflow' in c or 'inflow' in c.lower()]
    outflow_cols = [c for c in X.columns if 'Outflow' in c or 'outflow' in c.lower()]

    X['Net_Inflows_Current'] = X[inflow_cols].sum(axis=1) if inflow_cols else 0
    X['Net_Outflows_Current'] = X[outflow_cols].sum(axis=1) if outflow_cols else 0
    X['Net_Cash_Flow'] = X['Net_Inflows_Current'] - X['Net_Outflows_Current']
    X['Lag1_Ending'] = y.shift(1)
    X['Lag2_Ending'] = y.shift(2)
    X['Rolling3_NetCash'] = X['Net_Cash_Flow'].rolling(window=3, min_periods=1).mean()
    X = X.fillna(0)
    return X, y, target_col


class CashFlowPredictor:
    """Trains LMX + MetaDES stack on official cash flow statements."""

    def __init__(self, dataset_path=DEFAULT_DATASET):
        self.ready = False
        self.training_rows = 0
        self.training_metrics = []
        self.best_model = None
        self.best_r2 = -999
        self.model_comparison_chart = None
        self.scaler = None
        self.meta_model = None
        self.meta_des = None
        self.kbins = None
        self.pool_classifiers = []
        self.base_models = {}
        self.feature_columns = None
        self.target_col = None
        self._train(dataset_path)

    def _adapt_splits(self, n_rows):
        if n_rows < 12:
            return 2, 0.15, 200, 200
        if n_rows < 24:
            return 3, 0.2, 400, 300
        return 5, 0.25, 1200, 500

    def _train(self, dataset_path):
        try:
            if not os.path.exists(dataset_path):
                print(f'Cash flow dataset not found: {dataset_path}')
                return

            raw = pd.read_csv(dataset_path)
            pivot_df = _normalize_official_df(raw)
            X, y, target_col = _engineer_features(pivot_df)
            self.feature_columns = list(X.columns)
            self.target_col = target_col
            self.training_rows = len(X)

            n_splits, test_size, lgbm_est, rf_est = self._adapt_splits(len(X))
            split_idx = max(3, int(len(X) * (1 - test_size)))

            X_train = X.iloc[:split_idx]
            X_test = X.iloc[split_idx:]
            y_train = y.iloc[:split_idx]
            y_test = y.iloc[split_idx:]

            self.scaler = StandardScaler()
            X_train_s = self.scaler.fit_transform(X_train)
            X_test_s = self.scaler.transform(X_test)

            tscv = TimeSeriesSplit(n_splits=n_splits)

            lgbm = self._try_import_lgbm(lgbm_est)
            xgb = self._try_import_xgb(lgbm_est)
            rf = RandomForestRegressor(n_estimators=rf_est, max_depth=9, min_samples_leaf=3, n_jobs=-1, random_state=42)
            dt = DecisionTreeRegressor(max_depth=4, random_state=42)
            knn = KNeighborsRegressor(n_neighbors=min(8, max(2, len(X_train) // 3)), weights='distance')

            models = {}
            if lgbm:
                lgbm.fit(X_train_s, y_train)
                models['LGBM'] = lgbm
            if xgb:
                xgb.fit(X_train_s, y_train)
                models['XGB'] = xgb
            rf.fit(X_train_s, y_train)
            dt.fit(X_train_s, y_train)
            knn.fit(X_train_s, y_train)
            models.update({'RandomForest': rf, 'Decision Tree': dt, 'KNN': knn})
            self.base_models = models

            preds = {name: m.predict(X_test_s) for name, m in models.items()}

            if lgbm and xgb:
                oof_lgbm = _get_oof_predictions(lgbm, X_train_s, y_train, tscv)
                oof_xgb = _get_oof_predictions(xgb, X_train_s, y_train, tscv)
                meta_X_train = np.column_stack([X_train_s, oof_lgbm, oof_xgb])
                meta_X_test = np.column_stack([X_test_s, preds['LGBM'], preds['XGB']])
                self.meta_model = Ridge(alpha=1.0, random_state=42)
                self.meta_model.fit(meta_X_train, y_train)
                preds['LMX'] = self.meta_model.predict(meta_X_test)

            try:
                from deslib.des.meta_des import METADES
                n_bins = min(5, max(2, len(y_train) // 4))
                self.kbins = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='quantile')
                y_train_bins = self.kbins.fit_transform(y_train.values.reshape(-1, 1)).ravel()
                self.pool_classifiers = [
                    KNeighborsClassifier(n_neighbors=k)
                    for k in [7, 11, 15] if k < len(X_train)
                ] or [KNeighborsClassifier(n_neighbors=max(2, len(X_train) // 2))]
                for clf in self.pool_classifiers:
                    clf.fit(X_train_s, y_train_bins)
                self.meta_des = METADES(
                    pool_classifiers=self.pool_classifiers,
                    k=min(7, max(2, len(X_train) // 2)),
                )
                self.meta_des.fit(X_train_s, y_train_bins)
                des_labels = self.meta_des.predict(X_test_s)
                if lgbm:
                    preds['MetaDES'] = np.where(
                        des_labels < 2,
                        preds['LGBM'],
                        0.5 * preds['LGBM'] + 0.5 * preds['RandomForest'],
                    )
            except Exception as e:
                print('MetaDES skipped:', e)

            results = []
            for name, pred in preds.items():
                r2, rmse, mape = _evaluate(y_test, pred)
                results.append({'model': name, 'r2': r2, 'rmse': rmse, 'mape': mape})
                if r2 > self.best_r2:
                    self.best_r2 = r2
                    self.best_model = name

            results.sort(key=lambda x: x['r2'], reverse=True)
            self.training_metrics = results
            self.model_comparison_chart = self._build_comparison_chart(results)
            self.ready = True
            print(f'CashFlowPredictor trained on {self.training_rows} periods. Best: {self.best_model}')
        except Exception as e:
            print('CashFlowPredictor training failed:', e)
            import traceback
            traceback.print_exc()
            self.ready = False

    def _try_import_lgbm(self, n_estimators):
        try:
            from lightgbm import LGBMRegressor
            return LGBMRegressor(
                n_estimators=n_estimators, learning_rate=0.02, max_depth=7, num_leaves=63,
                subsample=0.85, colsample_bytree=0.85, reg_alpha=0.1, reg_lambda=0.1,
                random_state=42, verbosity=-1,
            )
        except ImportError:
            return None

    def _try_import_xgb(self, n_estimators):
        try:
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=n_estimators, learning_rate=0.02, max_depth=7,
                subsample=0.85, colsample_bytree=0.85, reg_alpha=0.1, reg_lambda=0.1,
                random_state=42, eval_metric='rmse',
            )
        except ImportError:
            return None

    def _build_comparison_chart(self, results):
        fig, ax = plt.subplots(figsize=(10, 5))
        names = [r['model'] for r in results]
        r2_vals = [r['r2'] for r in results]
        colors = ['#22c55e' if 'LMX' in n else '#3b82f6' for n in names]
        ax.bar(names, r2_vals, color=colors)
        ax.set_title('Model Comparison — R² Score (Ending Balance)')
        ax.set_ylabel('R²')
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        return _chart_to_base64(fig)

    def _align_features(self, X):
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        return X[self.feature_columns]

    def predict_user_series(self, pivot_df):
        if not self.ready:
            return None

        X, y, _ = _engineer_features(pivot_df)
        X = self._align_features(X)
        X_s = self.scaler.transform(X)

        preds = {name: model.predict(X_s) for name, model in self.base_models.items()}

        final_pred = preds.get('RandomForest')
        if self.meta_model and 'LGBM' in preds and 'XGB' in preds:
            meta_X = np.column_stack([X_s, preds['LGBM'], preds['XGB']])
            preds['LMX'] = self.meta_model.predict(meta_X)
            final_pred = preds['LMX']

        if self.meta_des and 'LGBM' in preds:
            try:
                des_labels = self.meta_des.predict(X_s)
                preds['MetaDES'] = np.where(
                    des_labels < 2,
                    preds['LGBM'],
                    0.5 * preds['LGBM'] + 0.5 * preds['RandomForest'],
                )
                if self.best_model == 'MetaDES':
                    final_pred = preds['MetaDES']
            except Exception:
                pass

        if self.best_model in preds:
            final_pred = preds[self.best_model]

        last_row = X.iloc[[-1]]
        last_ending = float(y.iloc[-1])
        last_row_s = self.scaler.transform(last_row)
        next_base = {n: float(m.predict(last_row_s)[0]) for n, m in self.base_models.items()}
        next_pred = next_base.get('RandomForest', last_ending)
        if self.meta_model and 'LGBM' in next_base and 'XGB' in next_base:
            meta_next = np.column_stack([last_row_s, [next_base['LGBM']], [next_base['XGB']]])
            next_pred = float(self.meta_model.predict(meta_next)[0])

        # Actual vs predicted chart for user data
        fig, ax = plt.subplots(figsize=(10, 5))
        dates = pivot_df['DATE'].astype(str).tolist()
        ax.plot(dates, y.tolist(), marker='o', label='Actual Ending Balance', linewidth=2)
        ax.plot(dates, final_pred.tolist(), marker='s', label=f'Predicted ({self.best_model})', linewidth=2, linestyle='--')
        ax.set_title('Cash Flow Ending Balance — Actual vs Predicted')
        ax.set_xlabel('Period')
        ax.set_ylabel('Ending Balance')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        forecast_chart = _chart_to_base64(fig)

        return {
            'historical': {
                'dates': dates,
                'actual': [round(float(v), 2) for v in y.tolist()],
                'predicted': [round(float(v), 2) for v in final_pred.tolist()],
            },
            'forecast': {
                'next_ending_balance': round(next_pred, 2),
                'last_ending_balance': round(last_ending, 2),
                'change': round(next_pred - last_ending, 2),
                'trend': 'up' if next_pred >= last_ending else 'down',
            },
            'best_model': self.best_model,
            'model_metrics': self.training_metrics,
            'model_chart': self.model_comparison_chart,
            'forecast_chart': forecast_chart,
        }


_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = CashFlowPredictor()
    return _predictor


def run_prediction_from_dataframe(raw_df):
    if _is_official_format(raw_df):
        pivot_df = _normalize_official_df(raw_df)
    else:
        pivot_df = _normalize_simple_df(raw_df)

    if len(pivot_df) < 3:
        return {
            'warning': 'Very little data — prediction may be unreliable. Upload at least 3 months.',
            'periods': len(pivot_df),
        }

    predictor = get_predictor()
    if not predictor.ready:
        return {'warning': 'Prediction model is not ready. Check server logs.'}

    return predictor.predict_user_series(pivot_df)


def run_prediction_from_csv(csv_path=None, manual_data=None):
    if csv_path:
        raw = pd.read_csv(csv_path)
    elif manual_data:
        raw = pd.DataFrame(manual_data)
    else:
        raise ValueError('CSV file or manual data required.')
    return run_prediction_from_dataframe(raw)
