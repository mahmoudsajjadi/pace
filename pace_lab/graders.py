"""pace_lab.graders: answer extraction and grading for multiple choice, math and hidden-profile items (standard library; sympy optional).

THE RULES (also the contract the unit tests check)

1. Final-answer rule. An "explicit final answer" is (a) the contents of a brace-balanced \\boxed{...} or \\fbox{...}, or (b) the payload of an
   answer marker: "Answer:", "Final answer:", "the answer is", "the correct answer/option/choice is", "= " is NOT a marker. When a response contains
   several explicit final answers, the one that appears LAST in the text wins (a model that corrects itself is graded on its correction). The grade
   records `conflict=True` when earlier explicit answers differ from the winner, so conflicts can be counted and hand-checked. Nothing is guessed:
   when there is no explicit answer the extractor falls back only where stated below, otherwise it returns None and the item is incorrect.
2. Multiple choice. The letter (A-J, limited to the number of options) is read from the winning candidate: "C", "(C)", "**C**", "C.", "Option C",
   "\\text{C}", "\\boxed{C}". If there is no marker or box, the last non-empty line is accepted only if it is a bare letter ("C", "(C)", "**C.**",
   "Option C"). The words "A" and "I" followed by a lowercase word ("Answer: A student ...", "Answer: I think") are not letters. Lowercase letters
   count only when the whole payload is that single letter.
3. Math. The winning candidate is normalised (see `normalize_math`) and compared with the gold answer by `math_equal`: identical normalised
   strings; else value equivalence of parsed expressions (exact rationals, floats with rel. tolerance 1e-9, and for expressions with variables
   six seeded random points; with sympy installed, `Expr.equals` may additionally veto a numeric match); sequences / tuples / intervals element by
   element in order with identical brackets; equations side by side. Decimal/fraction equality is by value: 0.5 = 1/2 = \\frac{1}{2}, 5.0 = 5.
   A percent sign is dropped ("50%" = 50, but 50% is NOT 0.5). A thousands separator is removed only in a whole-number pattern ("1,000" = 1000, while
   "(1,000)" stays a pair). Unicode minus signs map to "-", a leading word "minus"/"negative" maps to "-". A mixed number "2\\frac{1}{2}" means 2 + 1/2.
   Spelled-out numbers ("three") are NOT converted. Optional `allow_last_number_fallback` (off by default) takes the last number in the response.
4. Hidden profile. The candidate is the one name (Avery, Blake, Casey, Drew) in the winning explicit-answer payload, ignoring names that follow
   "not", "rather than", "instead of" or "unlike"; two different remaining names make the answer ambiguous (None). With no explicit answer the last
   non-empty line is used if it contains exactly one candidate name; otherwise None.

Backend: this module never needs sympy. `SYMPY_AVAILABLE` says whether the optional veto is active (the studio venv does not have sympy at the time of
writing; the pure-Python evaluator below is the documented fallback and is what the tests exercise).
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

try:  # optional
    import sympy as _sp
    SYMPY_AVAILABLE = True
except Exception:  # pragma: no cover - depends on the environment
    _sp = None
    SYMPY_AVAILABLE = False

NAMES = ("Avery", "Blake", "Casey", "Drew")
LETTERS = "ABCDEFGHIJ"


@dataclass
class Grade:
    correct: bool
    extracted: Optional[str]          # raw payload of the winning explicit answer (None if none)
    normalized: Optional[str] = None
    method: str = "none"              # boxed | marker | last_line | last_number | none
    conflict: bool = False            # earlier explicit answers differ from the winner
    n_candidates: int = 0


# ----------------------------------------------------------------------------- shared extraction
def balanced_after(text: str, open_idx: int) -> Optional[str]:
    """Contents of the brace group whose '{' is at open_idx (text[open_idx] == '{'); None if unbalanced (e.g. truncated output)."""
    depth, j = 0, open_idx
    while j < len(text):
        c = text[j]
        if c == "\\" and j + 1 < len(text):      # an escaped brace (\{ or \}) does not count
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1: j]
        j += 1
    return None


_BOX = re.compile(r"\\(?:boxed|fbox)\s*\{")
_MARKER_STRICT = re.compile(r"(?i)\b(?:final\s+answer|correct\s+(?:answer|option|choice)|answer)\b\s*(?:\*\*|__)?\s*(?:(?:is|are|would\s+be|should\s+be)\b\s*:?|:)\s*(?:\*\*|__)?\s*")


def find_candidates(text: str) -> List[Tuple[int, str, str]]:
    """All explicit final answers as (position, kind, payload), in text order. kind is 'boxed' or 'marker'."""
    text = text or ""
    found: List[Tuple[int, str, str]] = []
    for m in _BOX.finditer(text):
        inner = balanced_after(text, m.end() - 1)
        if inner is not None:
            found.append((m.start(), "boxed", inner.strip()))
    for m in _MARKER_STRICT.finditer(text):
        rest = text[m.end():]
        rest = rest.lstrip(" \t")
        if rest.startswith("\n"):                       # "Answer:\nC"
            rest = rest.lstrip()
        line = rest.split("\n", 1)[0]
        if _BOX.search(line):                           # the box is its own candidate
            continue
        payload = line.strip()
        if payload:
            found.append((m.start(), "marker", payload))
    found.sort(key=lambda x: x[0])
    return found


def _strip_md(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^[\s*_`>]+", "", s)
    s = re.sub(r"[\s*_`]+$", "", s)
    return s


# ----------------------------------------------------------------------------- multiple choice
def _letter_from(payload: str, n_options: int) -> Optional[str]:
    s = payload.strip()
    s = re.sub(r"^\\text(?:bf)?\s*\{(.*)\}$", r"\1", s).strip()
    bold = s.startswith(("*", "_", "("))
    s = re.sub(r"^[\s*_`$(\[]+", "", s)
    s = re.sub(r"(?i)^(?:option|choice|answer)\s*[:\-]?\s*", "", s)
    s = re.sub(r"^[\s*_`$(\[]+", "", s)
    s = re.sub(r"^\\text(?:bf)?\s*\{([^}]*)\}", r"\1", s)
    m = re.match(r"([A-Za-z])(?![A-Za-z0-9])", s)
    if not m:
        return None
    ch = m.group(1)
    after = s[m.end():]
    if ch.islower():
        return ch.upper() if re.fullmatch(r"[\s.)*_`$\]}:]*", after) and ch.upper() in LETTERS[:n_options] else None
    if ch not in LETTERS[:n_options]:
        return None
    if ch in "AI" and not bold:
        nxt = re.match(r"\s+([A-Za-z]+)", after)
        if nxt and nxt.group(1)[0].islower() and nxt.group(1).lower() not in ("because", "since", "as", "is", "and", "or", "but"):
            return None
    return ch


def extract_mc_letter(text: str, n_options: int = 10) -> Grade:
    """Letter of the last explicit answer (rule 2). Returns a Grade-like record with correct=False; use grade_mc to compare with gold."""
    cands = find_candidates(text)
    letters = [(pos, kind, pay, _letter_from(pay, n_options)) for pos, kind, pay in cands]
    letters = [x for x in letters if x[3]]
    if letters:
        pos, kind, pay, letter = letters[-1]
        conflict = any(x[3] != letter for x in letters[:-1])
        return Grade(False, pay, letter, kind, conflict, len(letters))
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if lines:
        last = _strip_md(lines[-1])
        m = re.fullmatch(r"(?i:option\s+)?\(?([A-J])\)?[.):]?", last)
        if m and m.group(1) in LETTERS[:n_options]:
            return Grade(False, lines[-1].strip(), m.group(1), "last_line", False, 1)
    return Grade(False, None, None, "none", False, 0)


def grade_mc(text: str, gold: str, n_options: int = 10) -> Grade:
    g = extract_mc_letter(text, n_options)
    g.correct = g.normalized is not None and g.normalized == str(gold).strip().upper()
    return g


# ----------------------------------------------------------------------------- math: normalisation
_UNICODE_MINUS = "\u2212\u2012\u2796\ufe63\uff0d"
_UNITS = ("degrees", "degree", "deg", "cm", "mm", "km", "m", "inches", "inch", "feet", "foot", "ft", "units", "unit", "square units", "sq units", "meters", "meter",
          "dollars", "dollar", "cents", "cent", "hours", "hour", "minutes", "minute", "seconds", "second", "mph", "days", "day", "years", "year", "percent",
          "pounds", "ounces", "gallons", "liters", "miles", "mile", "yards", "yard", "sq ft", "cubic units", "radians", "radian")
_NUM_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"


def _unwrap_commands(s: str) -> str:
    """\\text{x}, \\textbf{x}, \\mathrm{x}, \\mbox{x}, \\boxed{x} -> x (brace-balanced)."""
    pat = re.compile(r"\\(?:text|textbf|textit|mathrm|mathbf|mbox|boxed|fbox|operatorname)\s*\{")
    while True:
        m = pat.search(s)
        if not m:
            return s
        inner = balanced_after(s, m.end() - 1)
        if inner is None:
            return s[: m.start()] + s[m.end():]
        end = m.end() + len(inner) + 1
        s = s[: m.start()] + inner + s[end:]


def normalize_math(s: str) -> str:
    """Canonical string for comparing math answers (rule 3). Total: never raises, returns '' for empty input."""
    if s is None:
        return ""
    s = str(s).strip()
    # drop a trailing unit written as \text{ cm} / \mbox{ units} after a number, before text is unwrapped
    s = re.sub(r"(" + _NUM_RE + r")\s*\\(?:text|mbox|mathrm)\s*\{\s*[A-Za-z .^0-9]*\}\s*(?:\^\s*\{?\d\}?)?\s*$", r"\1", s)
    s = _unwrap_commands(s)
    for ch in _UNICODE_MINUS:
        s = s.replace(ch, "-")
    s = re.sub(r"^\s*[\u2013\u2014]\s*(?=[\d.\\(])", "-", s)       # en/em dash used as a leading minus
    s = s.replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
    s = s.replace("\\$", "").replace("$", "")
    s = s.replace("{,}", ",").replace("\\displaystyle", "")
    for tok in ("\\left", "\\right", "\\!", "\\,", "\\;", "\\:", "\\quad", "\\qquad", "\\ ", "\\;"):
        s = s.replace(tok, "")
    s = s.replace("dfrac", "frac").replace("tfrac", "frac")
    s = s.replace("\\%", "").replace("%", "").replace("^\\circ", "").replace("^{\\circ}", "").replace("\\circ", "").replace("\u00b0", "")
    s = s.strip()
    s = re.sub(r"(?i)^(?:minus|negative)\s+", "-", s)
    low = s.lower()
    for u in sorted(_UNITS, key=len, reverse=True):               # "5 degrees" -> "5" (only after a number)
        if re.fullmatch(_NUM_RE + r"\s*" + re.escape(u) + r"\.?", low):
            s = re.sub(r"\s*[A-Za-z ]+\.?$", "", s)
            break
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^[a-zA-Z]=(?=[^=]+$)", "", s)                    # "x=5" -> "5"
    s = re.sub(r"^(-?)(\d+)\\frac\{(\d+)\}\{(\d+)\}$", r"\1(\2+\\frac{\3}{\4})", s)   # mixed number
    s = re.sub(r"\\frac(\d)(\d)", r"\\frac{\1}{\2}", s)
    s = re.sub(r"\\sqrt(\d+)", r"\\sqrt{\1}", s)
    s = re.sub(r"\^(\d)(?=\d)", r"^{\1}", s)
    s = re.sub(r"[.\u3002]+$", "", s) if re.search(r"[\w)}]\.$", s) else s       # trailing period(s), not a lone "."
    if re.fullmatch(r"[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?", s):      # thousands separators, whole-number pattern only
        s = s.replace(",", "")
    m = re.fullmatch(r"\(([A-Za-z])\)", s)
    if m:
        s = m.group(1)
    if re.fullmatch(r"[A-Za-z]+", s):
        s = s.lower()
    return s


# ----------------------------------------------------------------------------- math: tiny expression engine
_TOKEN = re.compile(r"\d+(?:\.\d+)?|\.\d+|\\[A-Za-z]+|[A-Za-z]|[-+*/^()={}\[\],]")
_FUNCS = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "ln": math.log, "log": math.log10, "exp": math.exp}


class _ParseFail(Exception):
    pass


class _Parser:
    def __init__(self, s: str):
        pos, toks = 0, []
        while pos < len(s):
            m = _TOKEN.match(s, pos)
            if not m:
                raise _ParseFail("bad char %r" % s[pos])
            toks.append(m.group(0))
            pos = m.end()
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, expect=None):
        tok = self.peek()
        if tok is None or (expect is not None and tok != expect):
            raise _ParseFail("expected %s got %s" % (expect, tok))
        self.i += 1
        return tok

    def parse(self):
        node = self.expr()
        if self.peek() is not None:
            raise _ParseFail("trailing " + self.peek())
        return node

    def expr(self):
        node = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            node = ("add" if op == "+" else "sub", node, self.term())
        return node

    def _starts_atom(self, tok):
        if tok is None:
            return False
        return bool(re.fullmatch(r"\d+(?:\.\d+)?|\.\d+|[A-Za-z]|\(|\{", tok)) or tok in ("\\frac", "\\sqrt", "\\pi") or (tok.startswith("\\") and tok[1:] in _FUNCS)

    def term(self):
        node = self.unary()
        while True:
            tok = self.peek()
            if tok in ("*", "\\cdot", "\\times"):
                self.take()
                node = ("mul", node, self.unary())
            elif tok in ("/", "\\div"):
                self.take()
                node = ("div", node, self.unary())
            elif self._starts_atom(tok):
                node = ("mul", node, self.unary())            # implicit multiplication
            else:
                return node

    def unary(self):
        if self.peek() == "-":
            self.take()
            return ("neg", self.unary())
        if self.peek() == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "^":
            self.take()
            if self.peek() == "-":
                self.take()
                exp = ("neg", self.atom())
            else:
                exp = self.atom()
            return ("pow", base, exp)
        return base

    def group(self):
        if self.peek() == "{":
            self.take()
            node = self.expr()
            self.take("}")
            return node
        return self.atom()

    def atom(self):
        tok = self.peek()
        if tok is None:
            raise _ParseFail("unexpected end")
        if re.fullmatch(r"\d+(?:\.\d+)?|\.\d+", tok):
            self.take()
            return ("num", Fraction(tok))
        if tok == "\\pi":
            self.take()
            return ("pi",)
        if tok == "\\frac":
            self.take()
            a = self.group()
            b = self.group()
            return ("div", a, b)
        if tok == "\\sqrt":
            self.take()
            n = None
            if self.peek() == "[":
                self.take()
                n = self.expr()
                self.take("]")
            return ("sqrt", self.group(), n)
        if tok.startswith("\\") and tok[1:] in _FUNCS:
            self.take()
            arg = self.group() if self.peek() in ("{",) else (self.parenthesised() if self.peek() == "(" else self.atom())
            return ("fn", tok[1:], arg)
        if tok in ("(", "{"):
            return self.parenthesised()
        if re.fullmatch(r"[A-Za-z]", tok):
            self.take()
            return ("var", tok)
        raise _ParseFail("unexpected " + tok)

    def parenthesised(self):
        open_ = self.take()
        node = self.expr()
        self.take(")" if open_ == "(" else "}")
        return node


def parse_expr(s: str):
    """AST for a normalised latex-ish expression, or None when it is outside the supported grammar."""
    try:
        return _Parser(s).parse()
    except (_ParseFail, RecursionError):
        return None


def _free_vars(node, acc=None):
    acc = set() if acc is None else acc
    if node[0] == "var":
        acc.add(node[1])
    elif node[0] in ("add", "sub", "mul", "div", "pow"):
        _free_vars(node[1], acc)
        _free_vars(node[2], acc)
    elif node[0] in ("neg",):
        _free_vars(node[1], acc)
    elif node[0] == "sqrt":
        _free_vars(node[1], acc)
        if node[2] is not None:
            _free_vars(node[2], acc)
    elif node[0] == "fn":
        _free_vars(node[2], acc)
    return acc


def _pow(a, b):
    if isinstance(a, Fraction) and isinstance(b, Fraction) and b.denominator == 1 and abs(b.numerator) <= 4000:
        if a == 0 and b < 0:
            raise ZeroDivisionError
        return a ** int(b)
    r = float(a) ** float(b)
    if isinstance(r, complex):
        raise ValueError("complex")
    return r


def _root(a, n):
    if isinstance(a, Fraction) and isinstance(n, Fraction) and n.denominator == 1 and n > 0 and a >= 0:
        k = int(n)
        num, den = round(a.numerator ** (1.0 / k)), round(a.denominator ** (1.0 / k))
        if num ** k == a.numerator and den ** k == a.denominator:
            return Fraction(num, den)
    if float(a) < 0 and not (float(n) % 2 == 1):
        raise ValueError("even root of negative")
    f = abs(float(a)) ** (1.0 / float(n))
    return -f if float(a) < 0 else f


def _ev(node, env: Dict[str, Fraction]):
    k = node[0]
    if k == "num":
        return node[1]
    if k == "var":
        return env[node[1]]
    if k == "pi":
        return math.pi
    if k == "neg":
        return -_ev(node[1], env)
    if k == "add":
        return _ev(node[1], env) + _ev(node[2], env)
    if k == "sub":
        return _ev(node[1], env) - _ev(node[2], env)
    if k == "mul":
        return _ev(node[1], env) * _ev(node[2], env)
    if k == "div":
        d = _ev(node[2], env)
        if d == 0:
            raise ZeroDivisionError
        return _ev(node[1], env) / d
    if k == "pow":
        return _pow(_ev(node[1], env), _ev(node[2], env))
    if k == "sqrt":
        return _root(_ev(node[1], env), Fraction(2) if node[2] is None else _ev(node[2], env))
    if k == "fn":
        x = float(_ev(node[2], env))
        return _FUNCS[node[1]](x)
    raise ValueError(k)


def _close(a, b) -> bool:
    if isinstance(a, Fraction) and isinstance(b, Fraction):
        return a == b
    return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12)


def _to_sympy(node):  # pragma: no cover - only with sympy installed
    k = node[0]
    if k == "num":
        return _sp.Rational(node[1].numerator, node[1].denominator)
    if k == "var":
        return _sp.Symbol(node[1])
    if k == "pi":
        return _sp.pi
    if k == "neg":
        return -_to_sympy(node[1])
    if k in ("add", "sub", "mul", "div", "pow"):
        a, b = _to_sympy(node[1]), _to_sympy(node[2])
        return {"add": a + b, "sub": a - b, "mul": a * b, "div": a / b, "pow": a ** b}[k]
    if k == "sqrt":
        n = _sp.Integer(2) if node[2] is None else _to_sympy(node[2])
        return _to_sympy(node[1]) ** (1 / n)
    if k == "fn":
        return {"sin": _sp.sin, "cos": _sp.cos, "tan": _sp.tan, "ln": _sp.log, "exp": _sp.exp, "log": lambda x: _sp.log(x, 10)}[node[1]](_to_sympy(node[2]))
    raise ValueError(k)


def expr_equal(a, b) -> bool:
    """Equivalence of two ASTs: exact/float value without variables, six seeded points with variables; sympy may veto a match (Expr.equals is False)."""
    names = sorted(_free_vars(a) | _free_vars(b))
    rng = random.Random(2026)
    ok_points = 0
    for _ in range(12 if names else 1):
        env = {v: Fraction(rng.randint(2, 19), rng.randint(1, 5)) for v in names}
        try:
            va, vb = _ev(a, env), _ev(b, env)
        except (ZeroDivisionError, ValueError, OverflowError):
            continue
        if not _close(va, vb):
            return False
        ok_points += 1
        if ok_points >= 6:
            break
    if ok_points < (1 if not names else 3):
        return False
    if SYMPY_AVAILABLE:  # pragma: no cover
        try:
            verdict = (_to_sympy(a) - _to_sympy(b)).equals(0)
            if verdict is False:
                return False
        except Exception:
            pass
    return True


def _split_top(s: str, sep: str = ",") -> List[str]:
    out, depth, cur = [], 0, []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def _as_sequence(s: str) -> Optional[Tuple[str, str, List[str]]]:
    if len(s) >= 2 and s[0] in "([" and s[-1] in ")]":
        depth = 0
        for i, ch in enumerate(s):
            depth += ch in "([{"
            depth -= ch in ")]}"
            if depth == 0 and i < len(s) - 1:
                break
        else:
            items = _split_top(s[1:-1])
            if len(items) > 1:
                return s[0], s[-1], items
            return None
    items = _split_top(s)
    return ("", "", items) if len(items) > 1 else None


def _equal_norm(a: str, b: str) -> bool:
    if a == b:
        return True
    if not a or not b:
        return False
    sa, sb = _as_sequence(a), _as_sequence(b)
    if sa or sb:
        return bool(sa and sb and sa[0] == sb[0] and sa[1] == sb[1] and len(sa[2]) == len(sb[2]) and all(_equal_norm(x, y) for x, y in zip(sa[2], sb[2])))
    if a.count("=") == 1 and b.count("=") == 1:
        (la, ra), (lb, rb) = a.split("="), b.split("=")
        return _equal_norm(la, lb) and _equal_norm(ra, rb)
    ea, eb = parse_expr(a), parse_expr(b)
    if ea is None or eb is None:
        return False
    return expr_equal(ea, eb)


def math_equal(pred: Optional[str], gold: Optional[str]) -> bool:
    """Is the predicted answer equivalent to the gold answer (rule 3)? Both sides pass through normalize_math."""
    if pred is None or gold is None:
        return False
    return _equal_norm(normalize_math(pred), normalize_math(gold))


# ----------------------------------------------------------------------------- math: extraction and grading
_LAST_NUMBER = re.compile(r"[-\u2212]?\d[\d,]*(?:\.\d+)?")


def extract_math_answer(text: str, allow_last_number_fallback: bool = False) -> Grade:
    cands = find_candidates(text)
    cands = [c for c in cands if c[2]]
    if cands:
        pos, kind, payload = cands[-1]
        norm = normalize_math(_strip_md(payload) if kind == "marker" else payload)
        conflict = any(normalize_math(_strip_md(p) if k == "marker" else p) != norm for _, k, p in cands[:-1])
        return Grade(False, payload, norm, kind, conflict, len(cands))
    if allow_last_number_fallback:
        nums = _LAST_NUMBER.findall(text or "")
        if nums:
            return Grade(False, nums[-1], normalize_math(nums[-1]), "last_number", False, 0)
    return Grade(False, None, None, "none", False, 0)


def grade_math(text: str, gold: str, allow_last_number_fallback: bool = False) -> Grade:
    g = extract_math_answer(text, allow_last_number_fallback)
    g.correct = g.normalized is not None and gold is not None and _equal_norm(g.normalized, normalize_math(gold))
    return g


# ----------------------------------------------------------------------------- hidden profile
_NEG = re.compile(r"(?i)\b(?:not|rather\s+than|instead\s+of|unlike|except|over)\s+(?:\*\*)?(avery|blake|casey|drew)\b")


def _names_in(payload: str, names: Sequence[str] = NAMES) -> List[str]:
    s = _NEG.sub(" ", payload)
    found = []
    for m in re.finditer(r"(?i)\b(" + "|".join(map(re.escape, names)) + r")\b", s):
        nm = next(n for n in names if n.lower() == m.group(1).lower())
        if nm not in found:
            found.append(nm)
    return found


def extract_candidate(text: str, names: Sequence[str] = NAMES) -> Grade:
    """Candidate name chosen by the response (rule 4). `normalized` holds the canonical-cased name or None."""
    cands = find_candidates(text)
    scored = []
    for pos, kind, payload in cands:
        got = _names_in(payload, names)
        if got:
            scored.append((pos, kind, payload, got))
    if scored:
        pos, kind, payload, got = scored[-1]
        conflict = any(x[3] != got for x in scored[:-1])
        if len(got) == 1:
            return Grade(False, payload, got[0], kind, conflict, len(scored))
        return Grade(False, payload, None, kind, True, len(scored))               # two names in one final answer: ambiguous
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if lines:
        got = _names_in(lines[-1], names)
        if len(got) == 1:
            return Grade(False, lines[-1].strip(), got[0], "last_line", False, 1)
    return Grade(False, None, None, "none", False, 0)


def grade_hidden_profile(text: str, gold: str, names: Sequence[str] = NAMES) -> Grade:
    g = extract_candidate(text, names)
    g.correct = g.normalized is not None and g.normalized.lower() == str(gold).strip().lower()
    return g


# ----------------------------------------------------------------------------- dispatcher
def grade_item(item: dict, text: str) -> Grade:
    """Grade a response against an item of the pace_lab.data schema ('kind' is 'mc', 'num' or 'name')."""
    kind = item["kind"]
    if kind == "mc":
        return grade_mc(text, item["gold"], int(item.get("meta", {}).get("n_options", 10)))
    if kind == "num":
        return grade_math(text, item["gold"])
    if kind == "name":
        return grade_hidden_profile(text, item["gold"])
    raise ValueError("no grader for kind %r" % kind)
