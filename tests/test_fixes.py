"""Tests for high-priority security and business logic fixes."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_funding_optimizer import analyze_funding
from ensemble_models import predict_risk, get_risk_models


class DummyModel:
    def predict(self, X):
        return [0]


class DummyScaler:
    def transform(self, X):
        return X


class DummyLE:
    def inverse_transform(self, y):
        return ['low']


def test_growth_rate_uses_percent():
    """Growth rate 5 should mean 5%, not 500%."""
    called = {}

    def fake_predict(inflow, outflow, net_flow, profitability, stability):
        called['inflow'] = inflow
        return 'low'

    with patch('ai_funding_optimizer.predict_risk', side_effect=fake_predict):
        analyze_funding(
            funding=100000, capital=50000, revenue=10000, expenses=8000,
            growth_rate=5, duration=12,
            flow_model=DummyModel(), scaler=DummyScaler(),
            scale_info={'scale_factor': 1.0},
        )

    assert called['inflow'] == pytest.approx(10500.0)


def test_predict_risk_uses_cached_models():
    fake_cache = (DummyModel(), DummyScaler(), DummyLE())
    with patch('ensemble_models._risk_models', fake_cache):
        with patch('ensemble_models.joblib.load') as load_mock:
            result = predict_risk(1000, 800, 200, 0.2, 0.8)
            load_mock.assert_not_called()
            assert result == 'low'


def test_get_risk_models_returns_singleton():
    fake_cache = (DummyModel(), DummyScaler(), DummyLE())
    with patch('ensemble_models._risk_models', fake_cache):
        a = get_risk_models()
        b = get_risk_models()
        assert a is b
