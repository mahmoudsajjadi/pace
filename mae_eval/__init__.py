"""mae-eval: compute-accounting and audit utilities for multi-agent LLM evaluations (prototype).

See docs/MAEO_SPECIFICATION.md. Prototype status: no provider price table is bundled; register prices explicitly.
"""
from .auditor import ComputeParityError, EvaluationAuditor, Flag
from .tracker import CallRecord, PricingUnavailable, ResourceTracker, Session
from .vector import ControlState, ResourceVector, ResourceVectorError

__version__ = "0.1.0"
__all__ = ["ResourceTracker", "EvaluationAuditor", "ResourceVector", "ControlState", "ResourceVectorError",
           "ComputeParityError", "PricingUnavailable", "Flag", "Session", "CallRecord"]
