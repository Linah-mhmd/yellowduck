"""Tests for portfolio public credibility track."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_routes import _project_share_pct


def test_share_pct_prefers_stored_share():
    project = {'amount': '100000'}
    inv = {'share': 12.5, 'amount': 5000}
    assert _project_share_pct(project, inv) == 12.5


def test_share_pct_computed_from_amount():
    project = {'amount': '100000'}
    inv = {'share': 0, 'amount': 25000}
    assert _project_share_pct(project, inv) == 25.0


def test_share_pct_capped_at_100():
    project = {'amount': '1000'}
    inv = {'share': 150}
    assert _project_share_pct(project, inv) == 100.0
