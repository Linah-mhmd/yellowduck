import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cash_flow_predictor import CashFlowPredictor

p = CashFlowPredictor()
print('ready', p.ready)
if p.ready:
    print('rows', p.training_rows)
    print('metrics', p.training_metrics[:3])
    print('best', p.best_model)
