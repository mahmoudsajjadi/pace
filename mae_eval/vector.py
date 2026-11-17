"""ResourceVector: the 6-dimensional resource-accounting vector R of the MAEO specification (docs/MAEO_SPECIFICATION.md, section 2).

R = <r_reason, r_token, r_cost, r_lat, r_sample, r_sys>. A field set to None means "unreported" (the fourth control state).
Scaffold tokens (system prompts, role declarations, echoed message history) are tracked separately as r_scaffold and are
counted INSIDE r_token; reasoning tokens are counted inside completion tokens, and r_token = prompt + completion.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Dict, Optional

DIMENSIONS = ("r_reason", "r_token", "r_cost", "r_lat", "r_sample", "r_sys")
_INT_DIMS = {"r_sample", "r_sys"}


class ControlState(str, Enum):
    """How a resource dimension is controlled between a multi-agent system and its single-agent baseline."""
    STRICT = "Strictly Controlled"
    APPROXIMATE = "Approximately Matched"
    UNMATCHED = "Unmatched (Measured)"
    UNREPORTED = "Unreported (Omitted)"


class ResourceVectorError(ValueError):
    """Raised when a ResourceVector violates the specification."""


@dataclass
class ResourceVector:
    r_reason: Optional[float] = None   # total reasoning / scratchpad tokens
    r_token: Optional[float] = None    # total prompt + completion tokens (includes scaffold)
    r_cost: Optional[float] = None     # total monetary inference cost, USD
    r_lat: Optional[float] = None      # wall-clock latency in seconds (makespan, concurrency-aware)
    r_sample: Optional[int] = None     # total model completions drawn
    r_sys: Optional[int] = None        # tool invocations / search queries
    r_scaffold: Optional[float] = None # scaffold tokens (subset of r_token); not part of the 6-vector

    # ---- derived ----
    @property
    def scaffold_pct(self) -> Optional[float]:
        """Scaffold tokens as a percentage of r_token; None if either is unreported or r_token is 0."""
        if self.r_scaffold is None or not self.r_token:
            return None
        return 100.0 * self.r_scaffold / self.r_token

    # ---- serialization ----
    def to_dict(self, include_scaffold: bool = False) -> Dict[str, Any]:
        d = {k: getattr(self, k) for k in DIMENSIONS}
        if include_scaffold:
            d["r_scaffold"] = self.r_scaffold
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResourceVector":
        known = {f.name for f in fields(cls)}
        extra = set(d) - known
        if extra:
            raise ResourceVectorError("unknown resource fields: %s" % sorted(extra))
        return cls(**{k: d.get(k) for k in known if k in d})

    # ---- validation against the MAEO submission schema ----
    def validate(self, strict: bool = True) -> "ResourceVector":
        """Check the vector against docs/MAEO_SPECIFICATION.md section 2.

        strict=True (submission mode): every dimension must be present (not None).
        strict=False (audit mode): None is allowed and means 'unreported'.
        Always: numbers must be finite and non-negative; r_sample and r_sys must be integers; r_sample >= 1 when given;
        r_reason <= r_token and r_scaffold <= r_token when those are given.
        """
        for name in DIMENSIONS:
            v = getattr(self, name)
            if v is None:
                if strict:
                    raise ResourceVectorError("%s is required for a submission (use None only for audit mode)" % name)
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ResourceVectorError("%s must be a number, got %r" % (name, type(v).__name__))
            if not math.isfinite(v) or v < 0:
                raise ResourceVectorError("%s must be finite and >= 0, got %r" % (name, v))
            if name in _INT_DIMS and float(v) != int(v):
                raise ResourceVectorError("%s must be an integer, got %r" % (name, v))
        if self.r_sample is not None and self.r_sample < 1:
            raise ResourceVectorError("r_sample must be >= 1")
        if self.r_token is not None:
            for sub in ("r_reason", "r_scaffold"):
                val = getattr(self, sub)
                if val is not None and val > self.r_token:
                    raise ResourceVectorError("%s (%s) cannot exceed r_token (%s)" % (sub, val, self.r_token))
        return self
