"""Deterministic arithmetic verifier for Route II (an external check in the system's tool budget, R_sys > 0).

A response passes if it contains a line `Expression: <arithmetic expression>` and a line `Answer: <number>` and the expression, evaluated by a restricted parser, equals the answer.
The parser accepts numbers, the operators + - * / // % ** and parentheses, and nothing else: there are no names, calls, attributes or strings, and no code is executed (ast is used
only to parse). It checks that the calculation is consistent with the stated answer. It does not check that the expression models the problem, so a wrong plan with correct arithmetic
passes: the verifier is partial, with a false-positive rate for wrong answers above zero.
"""
from __future__ import annotations

import ast
import operator
import re
from fractions import Fraction
from typing import Optional, Tuple

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_NODES, MAX_EXP, MAX_ABS = 200, 12, 10 ** 15


def _clean(expr: str) -> str:
    e = expr.strip().strip("`$ ").rstrip(".")
    e = e.replace("\u00d7", "*").replace("\u00f7", "/").replace("\u2212", "-").replace("^", "**").replace("\\times", "*").replace("\\cdot", "*").replace("\\div", "/")
    e = re.sub(r"(?<=\d),(?=\d{3}\b)", "", e)                 # thousands separators
    e = re.sub(r"\$|\\left|\\right", "", e)
    e = re.sub(r"(\d+(?:\.\d+)?)\s*%(?=\s*(?:$|[-+*/)]))", r"(\1/100)", e)         # 12% -> (12/100) when % is a postfix; 7%4 stays a modulo
    return e


def safe_eval(expr: str) -> Fraction:
    """Evaluate an arithmetic expression exactly (Fraction); raises ValueError for anything outside the grammar or for oversized values."""
    tree = ast.parse(_clean(expr), mode="eval")
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise ValueError("expression too long")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return Fraction(str(n.value))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UN:
            return _UN[type(n.op)](ev(n.operand))
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow):
                if b.denominator != 1 or abs(b) > MAX_EXP:
                    raise ValueError("exponent not allowed")
                v = a ** int(b)
            elif isinstance(n.op, (ast.Div, ast.FloorDiv, ast.Mod)) and b == 0:
                raise ValueError("division by zero")
            else:
                v = _BIN[type(n.op)](a, b)
            if abs(v) > MAX_ABS:
                raise ValueError("value too large")
            return Fraction(v)
        raise ValueError("not an arithmetic expression")
    return ev(tree)


def _number(text: str) -> Optional[Fraction]:
    t = text.strip().strip("*$ ").rstrip(".").replace(",", "")
    t = re.sub(r"\\boxed\{(.*)\}", r"\1", t)
    t = re.sub(r"[A-Za-z%\\ ]+$", "", t).strip()            # trailing units
    try:
        if re.fullmatch(r"-?\d+/\d+", t):
            return Fraction(t)
        return Fraction(t)
    except (ValueError, ZeroDivisionError):
        return None


def parse_lines(text: str) -> Tuple[Optional[str], Optional[str]]:
    ex = re.findall(r"(?im)^\s*\**expression\**\s*:\s*(.+)$", text or "")
    an = re.findall(r"(?im)^\s*\**answer\**\s*:\s*(.+)$", text or "")
    return (ex[-1].strip() if ex else None, an[-1].strip() if an else None)


def verify(text: str) -> Tuple[bool, str]:
    """(passed, reason). Reasons: missing line, not arithmetic, answer not a number, mismatch, ok."""
    expr, ans = parse_lines(text)
    if expr is None or ans is None:
        return False, "missing expression or answer line"
    try:
        val = safe_eval(expr)
    except (SyntaxError, ValueError, ZeroDivisionError, RecursionError, OverflowError):
        return False, "not an arithmetic expression"
    a = _number(ans)
    if a is None:
        return False, "answer is not a number"
    d = len(re.sub(r"[^0-9.]", "", ans).partition(".")[2])        # an answer rounded to d decimals matches the exact value rounded to d decimals
    ok = val == a or (d > 0 and round(val, d) == a)
    return ok, "ok" if ok else "expression does not equal the answer"
