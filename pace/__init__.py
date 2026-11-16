"""cme: measure a multi-agent system against the self-consistency frontier at its measured token cost.

Commands: `pace proxy` (logging proxy), `pace baseline` (greedy + sample pool), `pace report` (frontier gap, resource card, table, figure).
Built on mae_eval (resource vector and parity auditor). Python API: pace.frontier_gap, pace.build_report, pace.resource_card, pace.wrap (log a client's usage without a proxy), pace.track (label items and rounds).
"""
from .frontier import Pool, frontier_at, frontier_curve, frontier_gap, pav_increasing
from .report import build_report, to_latex
from .client import wrap, track, log_result

__version__ = "0.1.0"
__all__ = ["Pool", "frontier_at", "frontier_curve", "frontier_gap", "pav_increasing", "build_report", "to_latex", "wrap", "track", "log_result"]
