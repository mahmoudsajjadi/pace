"""EvaluationAuditor: compares a multi-agent resource vector with its single-agent baseline and flags confounders."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Union

from .tracker import Session
from .vector import DIMENSIONS, ControlState, ResourceVector

# Default dimensions that must be matched for a parity claim, by the question being asked.
PARITY_DIMS_DEFAULT = ("r_token",)

_MESSAGES = {
    "r_sample": "sample counts differ: gains may reflect ensembling (more draws), not coordination",
    "r_reason": "reasoning-token budgets differ: thinking compute is not matched",
    "r_token": "total tokens differ: scaffold, history echoes, or extra calls consume more budget",
    "r_cost": "monetary cost differs: comparison is not cost-matched",
    "r_lat": "wall-clock latency differs (serialization or concurrency)",
    "r_sys": "tool or search invocations differ",
}


class ComputeParityError(AssertionError):
    """Raised by assert_compute_parity when a dimension is outside tolerance."""


@dataclass(frozen=True)
class Flag:
    dimension: str
    ratio: Optional[float]
    state: ControlState
    message: str


def _as_vector(x: Union[ResourceVector, Session]) -> ResourceVector:
    return x.get_resource_vector(allow_missing_pricing=True) if isinstance(x, Session) else x


class EvaluationAuditor:
    """mas / sas may be ResourceVector or a recorded Session.

    approx_tolerance: relative deviation up to which a dimension counts as 'Approximately Matched' (default 0.25).
    """

    def __init__(self, mas: Union[ResourceVector, Session], sas: Union[ResourceVector, Session, None] = None,
                 approx_tolerance: float = 0.25):
        self.mas = _as_vector(mas)
        self.sas = _as_vector(sas) if sas is not None else None
        self.approx_tolerance = approx_tolerance

    def _need_sas(self) -> ResourceVector:
        if self.sas is None:
            raise ValueError("a single-agent baseline is required for this operation")
        return self.sas

    def ratios(self) -> Dict[str, Optional[float]]:
        """MAS / SAS per dimension. None if either side is unreported or both are 0 (0/0 is undefined, printed as n/a); inf if the baseline is 0 and MAS is not."""
        sas = self._need_sas()
        out: Dict[str, Optional[float]] = {}
        for d in DIMENSIONS:
            m, s = getattr(self.mas, d), getattr(sas, d)
            if m is None or s is None:
                out[d] = None
            elif s == 0:
                out[d] = None if m == 0 else math.inf
            else:
                out[d] = m / s
        return out

    def control_states(self, tolerance: float = 0.05) -> Dict[str, ControlState]:
        states: Dict[str, ControlState] = {}
        sas = self._need_sas()
        for d, r in self.ratios().items():
            if r is None and getattr(self.mas, d) == 0 and getattr(sas, d) == 0:
                states[d] = ControlState.STRICT  # both systems consumed none: equal, but the ratio is undefined
            elif r is None:
                states[d] = ControlState.UNREPORTED
            else:
                dev = abs(r - 1.0)
                states[d] = (ControlState.STRICT if dev <= tolerance
                             else ControlState.APPROXIMATE if dev <= self.approx_tolerance
                             else ControlState.UNMATCHED)
        return states

    def flag_confounders(self, tolerance: float = 0.05) -> List[Flag]:
        """One Flag per dimension that is not strictly controlled, with an explanation."""
        ratios = self.ratios()
        flags = []
        for d, st in self.control_states(tolerance).items():
            if st is ControlState.STRICT:
                continue
            msg = _MESSAGES[d] if st is not ControlState.UNREPORTED else "not reported by one or both systems"
            flags.append(Flag(d, ratios[d], st, msg))
        return flags

    def assert_compute_parity(self, tolerance: float = 0.05, dims: Sequence[str] = PARITY_DIMS_DEFAULT) -> None:
        """Raise ComputeParityError unless every dimension in `dims` is reported and within `tolerance` of ratio 1."""
        bad = []
        ratios = self.ratios()
        for d in dims:
            if d not in DIMENSIONS:
                raise ValueError("unknown dimension %r" % d)
            r = ratios[d]
            if r is None and getattr(self.mas, d) == 0 and getattr(self._need_sas(), d) == 0:
                continue  # 0/0: both systems consumed none of this resource
            if r is None:
                bad.append("%s: unreported" % d)
            elif abs(r - 1.0) > tolerance:
                bad.append("%s: MAS/SAS = %.3f (tolerance %.3f)" % (d, r, tolerance))
        if bad:
            raise ComputeParityError("compute parity violated: " + "; ".join(bad))
