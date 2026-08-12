import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cash_flow import analyze_cash_flow
from cash_flow_predictor import CashFlowPredictor, run_prediction_from_dataframe


DATASET = Path(__file__).resolve().parents[1] / 'dataset' / 'Financial_Plan_Statements_-_Cash_Flow.csv'


@pytest.fixture(scope='module')
def predictor():
    return CashFlowPredictor(dataset_path=str(DATASET))


def test_predictor_trains(predictor):
    assert predictor.ready is True
    assert predictor.training_rows >= 12
    assert predictor.best_model in {'LMX', 'LGBM', 'XGB', 'RandomForest', 'MetaDES', 'Decision Tree', 'KNN'}
    assert len(predictor.training_metrics) >= 3


def test_analyze_official_csv():
    result = analyze_cash_flow(csv_file=str(DATASET))
    assert 'prediction' in result
    assert 'prediction_advice' in result
    assert 'funding' not in result
    assert result['prediction'].get('best_model')


def test_analyze_simple_manual_rows():
    rows = [
        {'month': 'January', 'fiscal year': '2025', 'inflows/outflows': 'Inflows', 'amount': 1000},
        {'month': 'January', 'fiscal year': '2025', 'inflows/outflows': 'Outflows', 'amount': 400},
        {'month': 'February', 'fiscal year': '2025', 'inflows/outflows': 'Inflows', 'amount': 1100},
        {'month': 'February', 'fiscal year': '2025', 'inflows/outflows': 'Outflows', 'amount': 450},
        {'month': 'March', 'fiscal year': '2025', 'inflows/outflows': 'Inflows', 'amount': 1200},
        {'month': 'March', 'fiscal year': '2025', 'inflows/outflows': 'Outflows', 'amount': 500},
    ]
    result = analyze_cash_flow(manual_data=rows)
    assert result['insights']
    assert 'prediction' in result
