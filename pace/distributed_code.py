"""Seed-controlled generator of distributed coding tasks (Escape Route II, Cell E2): distinct Python tasks whose complementary constraints are split across three agents.

Eight templates (list, string, dict, interval, graph, dynamic programming, parsing, validation) with randomised parameters. For every item:
  shared     the function name, signature and the part of the specification all agents see
  split      three agent prompts, each with the shared part plus ONE of the three complementary constraints (no agent can write the full function alone)
  prompt     the full specification (all three constraints), for the full-evidence reference arm
  reference  a reference solution (Python source of `solve`)
  gold       {"tests": [assert strings], "setup": ""}: executable unit tests, in the format cme.tasks.run_tests expects; kind is "code"
The tests are generated from the reference solution on random inputs; the reference passes them by construction (checked in the unit tests) and a function that ignores any one of the
three constraints fails them (checked in the unit tests with deliberately wrong variants). The items are SYNTHETIC ("synthetic": true). Pure standard library.
"""

from __future__ import annotations

import random

TEMPLATES = ["list", "string", "dict", "interval", "graph", "dp", "parsing", "validation"]


def _run(src: str):
    env: dict = {}
    exec(src, env)  # noqa: S102 - generated reference source, executed to compute expected values
    return env["solve"]


def _t_list(r: random.Random):
    t = r.randint(-20, 40)
    op = r.choice(["square", "cube", "double_plus"])
    k = r.randint(1, 9)
    desc = r.choice([True, False])
    opsrc = {"square": "x * x", "cube": "x * x * x", "double_plus": "2 * x + %d" % k}[op]
    opdesc = {"square": "replace each kept element by its square", "cube": "replace each kept element by its cube", "double_plus": "replace each kept element x by 2*x + %d" % k}[op]
    src = "def solve(xs):\n    ys = [%s for x in xs if x > %d]\n    return sorted(ys, reverse=%s)\n" % (opsrc, t, desc)
    cons = ["Keep only the elements that are strictly greater than %d." % t, "After filtering, %s." % opdesc, "Return the resulting list sorted in %s order." % ("descending" if desc else "ascending")]
    f = _run(src)
    inputs = [[r.randint(-30, 60) for _ in range(r.randint(0, 9))] for _ in range(7)]
    return "list of integers", "xs", src, cons, [((x,), f(x)) for x in inputs]


def _t_string(r: random.Random):
    k = r.randint(1, 25)
    upper = r.choice([True, False])
    period = r.randint(2, 6)
    base = "A" if upper else "a"
    src = ("def solve(s):\n    out = []\n    for i, c in enumerate(s):\n        if i %% %d != 0 and c.%s() and c.isalpha():\n            out.append(chr((ord(c) - ord('%s') + %d) %% 26 + ord('%s')))\n        else:\n            out.append(c)\n    return ''.join(out)\n"
           % (period, "isupper" if upper else "islower", base, k, base))
    kind = "uppercase" if upper else "lowercase"
    cons = ["Shift every %s letter forward in the alphabet by %d positions, with wrap-around from 'z' to 'a' (or 'Z' to 'A')." % (kind, k),
            "All other characters (including letters of the other case) stay unchanged.", "Characters at 0-based positions divisible by %d are never changed, whatever they are." % period]
    f = _run(src)
    alphabet = "abcxyzABCXYZ 09-_"
    inputs = ["".join(r.choice(alphabet) for _ in range(r.randint(0, 12))) for _ in range(8)]
    return "string", "s", src, cons, [((x,), f(x)) for x in inputs]


def _t_dict(r: random.Random):
    keep_min = r.choice([True, False])
    desc = r.choice([True, False])
    floor = r.randint(0, 18)
    src = ("def solve(d):\n    inv = {}\n    for k in sorted(d):\n        if k < %d:\n            continue\n        v = d[k]\n        if v not in inv:\n            inv[v] = k\n        else:\n            inv[v] = %s(inv[v], k)\n    return sorted(inv.items(), reverse=%s)\n"
           % (floor, "min" if keep_min else "max", desc))
    cons = ["Invert the mapping: every value of the input dict becomes a key and its original key becomes the value; entries whose original key is smaller than %d are ignored." % floor,
            "When several keys share a value, keep the %s key." % ("smallest" if keep_min else "largest"),
            "Return the inverted mapping as a list of (key, value) pairs sorted by key in %s order." % ("descending" if desc else "ascending")]
    f = _run(src)
    inputs = []
    for _ in range(8):
        keys = r.sample(range(0, 30), r.randint(0, 8))
        inputs.append({k: r.randint(1, 4) for k in keys})
    return "dict of int to int", "d", src, cons, [((x,), f(x)) for x in inputs]


def _t_interval(r: random.Random):
    g = r.randint(0, 9)
    m = r.randint(0, 6)
    src = ("def solve(iv):\n    out = []\n    for a, b in sorted(iv):\n        if out and a <= out[-1][1] + %d:\n            out[-1] = (out[-1][0], max(out[-1][1], b))\n        else:\n            out.append((a, b))\n    return [(a, b) for a, b in out if b - a >= %d]\n" % (g, m))
    cons = ["Merge intervals (pairs (start, end) with start <= end) that overlap.", "Also merge two intervals when the gap between them is at most %d (start of the next minus end of the previous)." % g,
            "Return a list of (start, end) tuples sorted by start, keeping only merged intervals with end - start >= %d." % m]
    f = _run(src)
    inputs = []
    for _ in range(8):
        iv = []
        for _ in range(r.randint(0, 7)):
            a = r.randint(0, 40)
            iv.append((a, a + r.randint(0, 8)))
        inputs.append(iv)
    return "list of (start, end) tuples", "iv", src, cons, [((x,), f(x)) for x in inputs]


def _t_graph(r: random.Random):
    directed = r.choice([True, False])
    none_val = r.choice([-1, 0, 99])
    cap = r.randint(2, 9)
    src = ("def solve(n, edges, src, dst):\n    adj = {i: [] for i in range(n)}\n    for a, b in edges:\n        adj[a].append(b)\n%s    dist = {src: 0}\n    queue = [src]\n    for u in queue:\n        for v in adj[u]:\n            if v not in dist:\n                dist[v] = dist[u] + 1\n                queue.append(v)\n    d = dist.get(dst)\n    return none_val if d is None or d > %d else d\n"
           % ("" if directed else "        adj[b].append(a)\n", cap)).replace("none_val", str(none_val))
    cons = ["Nodes are 0..n-1; return the minimum number of edges on a path from src to dst (breadth-first search).", "The edges are %s." % ("directed (a, b means a -> b)" if directed else "undirected (a, b can be used in both directions)"),
            "If dst cannot be reached from src, or the shortest path has more than %d edges, return %d." % (cap, none_val)]
    f = _run(src)
    cases = []
    for _ in range(8):
        n = r.randint(3, 10)
        edges = [(r.randrange(n), r.randrange(n)) for _ in range(r.randint(1, 11))]
        cases.append((n, edges, r.randrange(n), r.randrange(n)))
    return "n, edges, src, dst", "n, edges, src, dst", src, cons, [(c, f(*c)) for c in cases]


def _t_dp(r: random.Random):
    coins = sorted(r.sample([1, 2, 3, 4, 5, 6, 7, 10], r.randint(2, 4)))
    ordered = r.choice([True, False])
    mod = r.choice([1000007, 97, 1009, 10 ** 9 + 7])
    if ordered:
        body = "    dp = [1] + [0] * amount\n    for a in range(1, amount + 1):\n        for c in coins:\n            if c <= a:\n                dp[a] = (dp[a] + dp[a - c]) %% %d\n    return dp[amount]\n" % mod
    else:
        body = "    dp = [1] + [0] * amount\n    for c in coins:\n        for a in range(c, amount + 1):\n            dp[a] = (dp[a] + dp[a - c]) %% %d\n    return dp[amount]\n" % mod
    src = "def solve(amount):\n    coins = %s\n%s" % (coins, body)
    cons = ["Count the ways to make `amount` from unlimited coins of the denominations %s." % coins, "Two ways are %s." % ("different if the ORDER of the coins differs (sequences)" if ordered else "the same if they use the same coins in a different order (combinations)"),
            "Return the count modulo %d." % mod]
    f = _run(src)
    return "int amount", "amount", src, cons, [((a,), f(a)) for a in sorted({r.randint(0, 25) for _ in range(8)})]


def _t_parsing(r: random.Random):
    sep = r.choice([",", ";", "|"])
    prefix = r.choice(["a", "b", "k", "x"])
    use_prefix = r.choice([True, False])
    ln = r.randint(2, 6)
    skip_neg = r.choice([True, False])
    cond = "k.startswith(%r)" % prefix if use_prefix else "len(k) > %d" % ln
    neg = " and int(v) >= 0" if skip_neg else ""
    src = "def solve(s):\n    total = 0\n    for part in s.split(%r):\n        if not part:\n            continue\n        k, v = part.split('=')\n        if %s%s:\n            total += int(v)\n    return total\n" % (sep, cond, neg)
    cons = ["The input is a string of key=value pairs separated by %r; keys are lowercase words, values are integers (possibly negative)." % sep,
            "Sum the integer values of the pairs whose key %s." % (("starts with the letter %r" % prefix) if use_prefix else ("is longer than %d characters" % ln)),
            "Empty input or empty pieces contribute 0%s; return an int." % ("; pairs with a negative value are ignored" if skip_neg else "")]
    f = _run(src)
    words = ["a", "ab", "abc", "bee", "kilo", "xray", "kk", "bxyz", "axle", "abcdefg"]
    inputs = [sep.join("%s=%d" % (r.choice(words), r.randint(-9, 9)) for _ in range(r.randint(0, 7))) for _ in range(8)]
    return "string", "s", src, cons, [((x,), f(x)) for x in inputs]


def _t_validation(r: random.Random):
    pairs = r.choice([["()"], ["()", "[]"], ["()", "[]", "{}"], ["[]", "<>"]])
    empty_ok = r.choice([True, False])
    depth = r.randint(2, 6)
    opens = {p[0]: p[1] for p in pairs}
    src = ("def solve(s):\n    opens = %r\n    closes = set(opens.values())\n    if not s:\n        return %s\n    stack = []\n    for c in s:\n        if c in opens:\n            stack.append(opens[c])\n            if len(stack) > %d:\n                return False\n        elif c in closes:\n            if not stack or stack.pop() != c:\n                return False\n    return not stack\n" % (opens, str(empty_ok), depth))
    cons = ["Return True when the brackets %s in the string are balanced and correctly nested, otherwise False." % " ".join(pairs), "Characters that are not one of these brackets are ignored; nesting deeper than %d levels is invalid." % depth,
            "The empty string is %s." % ("valid (True)" if empty_ok else "invalid (False)")]
    f = _run(src)
    alphabet = "".join(pairs) + "ab "
    inputs = ["".join(r.choice(alphabet) for _ in range(r.randint(0, 12))) for _ in range(9)]
    return "string", "s", src, cons, [((x,), f(x)) for x in inputs]


_BUILDERS = {"list": _t_list, "string": _t_string, "dict": _t_dict, "interval": _t_interval, "graph": _t_graph, "dp": _t_dp, "parsing": _t_parsing, "validation": _t_validation}


def generate_items(n_items: int = 200, k_agents: int = 3, seed: int = 42) -> list[dict]:
    if n_items < 1:
        raise ValueError("n_items must be positive")
    if k_agents != 3:
        raise ValueError("distributed code benchmark requires exactly three agents")
    out, seen = [], set()
    index = attempts = 0
    while len(out) < n_items:
        attempts += 1
        if attempts > 50 * n_items:
            raise RuntimeError("could not generate %d distinct items (the parameter space is too small)" % n_items)
        template = TEMPLATES[index % len(TEMPLATES)]
        r = random.Random("%d:%d:%d" % (seed, index, attempts))
        arg_desc, sig, src, cons, cases = _BUILDERS[template](r)
        tests = ["assert solve(%s) == %r" % (", ".join(repr(a) for a in args), expected) for args, expected in cases]
        key = (template, tuple(cons))
        if key in seen or len(set(tests)) < 4:
            continue
        seen.add(key)
        shared = "Write a Python function `solve(%s)` (input: %s). Return the result only through the function; do not print." % (sig, arg_desc)
        label = len(out)
        order = list(range(3))
        r.shuffle(order)                                    # which constraint each agent holds is randomised, so agent identity carries no information
        split = [{"agent": a, "prompt": shared + " Your constraint: " + cons[order[a]] + " The other committee members hold the remaining constraints; the function must satisfy all of them."} for a in range(3)]
        out.append({"id": "code_%03d" % label, "route": "information_partitioning", "template": template, "kind": "code", "synthetic": True,
                    "shared": shared, "split": split, "constraints": [cons[i] for i in range(3)], "prompt": shared + " Constraints: " + " ".join("(%d) %s" % (i + 1, c) for i, c in enumerate(cons)),
                    "reference": src, "gold": {"tests": tests, "setup": ""}, "seed": seed})
        index += 1
    return out
