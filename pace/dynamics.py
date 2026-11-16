"""pace dynamics: how agents' answers change across debate rounds (standard library plus numpy).

Input: a JSONL file with one record per agent answer, {"item": str, "agent": str or int, "round": int, "correct": bool} and optionally "prompt_tokens" and
"completion_tokens". Nothing is estimated for missing fields: records without "correct" are ignored, and token statistics need both token fields.

Output (point estimates and 95% percentile intervals from a paired bootstrap that resamples items):
  flips between the first and the last round: wrong to right, right to wrong, right to right, wrong to wrong (counts, over item-agent pairs observed in both rounds);
  tau_ic = wrong-to-right / (all wrong in the first round) and tau_ci = right-to-wrong / (all right in the first round), the two rates of the conformity-to-truth model;
  p_star_hat = tau_ic / (tau_ic + tau_ci), the threshold implied by those rates (undefined if both rates are zero);
  p1 and p_last, the mean accuracy of an agent in the first and the last round;
  rho_total, the intraclass correlation of correctness across the agents of an item in each round (reported in the JSON also as rho_peer, its earlier name), and K_eff = K / (1 + (K - 1) rho_total)
  with rho_total clipped to [0, 1]; delta_rho_debate = rho_total(last round) - rho_total(first round), the excess correlation induced by debate, with its own bootstrap interval;
  mean tokens per call by round.
Limits: rho_total is the correlation of correctness among agents on the same item, so it includes shared item difficulty as well as correlated errors; the difference across rounds is the
quantity that isolates what the exchange of messages adds, and it is not a measure of error correlation between models. The tau
rates assume the constant-rate model of the paper; this command reports what the logs show under that model and does not test the model.
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np


def load(path: str):
    """Return {item: {agent: {round: correct}}} and {item: {round: [tokens per call]}}."""
    ans: dict[str, dict[str, dict[int, int]]] = defaultdict(lambda: defaultdict(dict))
    tok: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    with open(path, encoding="utf-8") as fh:
        for no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if (
                not isinstance(r, dict)
                or "correct" not in r
                or "round" not in r
                or "item" not in r
                or "agent" not in r
            ):
                continue
            ans[str(r["item"])][str(r["agent"])][int(r["round"])] = int(
                bool(r["correct"])
            )
            if (
                r.get("prompt_tokens") is not None
                and r.get("completion_tokens") is not None
            ):
                tok[str(r["item"])][int(r["round"])].append(
                    float(r["prompt_tokens"]) + float(r["completion_tokens"])
                )
    if not ans:
        raise ValueError(
            "no usable records: each line needs item, agent, round and correct"
        )
    return ans, tok


def icc(Z: np.ndarray) -> float | None:
    """One-way intraclass correlation of an items x agents 0/1 matrix (balanced)."""
    n, k = Z.shape
    if n < 2 or k < 2:
        return None
    m = Z.mean(axis=1)
    g = Z.mean()
    msb = k * np.sum((m - g) ** 2) / (n - 1)
    msw = np.sum((Z - m[:, None]) ** 2) / (n * (k - 1))
    den = msb + (k - 1) * msw
    return None if den == 0 else float((msb - msw) / den)


def stats(ans, items: list[str], r0: int, r1: int, rounds: list[int]) -> dict:
    wr = rw = rr = ww = 0
    a0 = []
    a1 = []
    for it in items:
        for ag, d in ans[it].items():
            if r0 in d and r1 in d:
                a, b = d[r0], d[r1]
                a0.append(a)
                a1.append(b)
                wr += a == 0 and b == 1
                rw += a == 1 and b == 0
                rr += a == 1 and b == 1
                ww += a == 0 and b == 0
    out = dict(
        wrong_to_right=wr, right_to_wrong=rw, right_to_right=rr, wrong_to_wrong=ww
    )
    out["tau_ic"] = wr / (wr + ww) if wr + ww else None
    out["tau_ci"] = rw / (rw + rr) if rw + rr else None
    ti, tc = out["tau_ic"], out["tau_ci"]
    out["p_star_hat"] = (
        ti / (ti + tc) if ti is not None and tc is not None and ti + tc > 0 else None
    )
    adj_wr = adj_rw = adj_rr = adj_ww = 0
    active_rounds = [r for r in rounds if r0 <= r <= r1]
    for it in items:
        for ag, d in ans[it].items():
            for r_a, r_b in zip(active_rounds[:-1], active_rounds[1:]):
                if r_a in d and r_b in d:
                    a, b = d[r_a], d[r_b]
                    adj_wr += a == 0 and b == 1
                    adj_rw += a == 1 and b == 0
                    adj_rr += a == 1 and b == 1
                    adj_ww += a == 0 and b == 0
    out["adjacent_wrong_to_right"] = adj_wr
    out["adjacent_right_to_wrong"] = adj_rw
    out["adjacent_right_to_right"] = adj_rr
    out["adjacent_wrong_to_wrong"] = adj_ww
    out["adjacent_tau_ic"] = adj_wr / (adj_wr + adj_ww) if adj_wr + adj_ww else None
    out["adjacent_tau_ci"] = adj_rw / (adj_rw + adj_rr) if adj_rw + adj_rr else None
    ati, atc = out["adjacent_tau_ic"], out["adjacent_tau_ci"]
    out["adjacent_p_star_hat"] = (
        ati / (ati + atc)
        if ati is not None and atc is not None and ati + atc > 0
        else None
    )
    out["p1"] = float(np.mean(a0)) if a0 else None
    out["p_last"] = float(np.mean(a1)) if a1 else None
    rho, keff = {}, {}
    for r in rounds:
        rows = [[d[r] for d in ans[it].values() if r in d] for it in items]
        k = min((len(x) for x in rows), default=0)
        Z = np.array([x[:k] for x in rows], dtype=float) if k >= 2 else None
        v = icc(Z) if Z is not None else None
        rho[r] = v
        keff[r] = (k / (1 + (k - 1) * min(1.0, max(0.0, v)))) if v is not None else None
    out["rho_peer"], out["rho_total"], out["k_eff"] = (
        rho,
        rho,
        keff,
    )  # rho_peer is the earlier name of rho_total
    out["delta_rho_debate"] = (
        (rho[r1] - rho[r0])
        if rho.get(r0) is not None and rho.get(r1) is not None
        else None
    )
    return out


def analyse(
    path: str,
    n_boot: int = 1000,
    seed: int = 0,
    first: int | None = None,
    last: int | None = None,
) -> dict:
    ans, tok = load(path)
    items = sorted(ans)
    rounds = sorted({r for it in items for d in ans[it].values() for r in d})
    if len(rounds) < 2:
        raise ValueError("need answers from at least two rounds; found %s" % rounds)
    r0, r1 = (
        (first if first is not None else rounds[0]),
        (last if last is not None else rounds[-1]),
    )
    if r0 not in rounds or r1 not in rounds or r0 >= r1:
        raise ValueError(
            "--first-round and --last-round must be distinct rounds present in the log, first < last; found rounds %s"
            % rounds
        )
    point = stats(ans, items, r0, r1, rounds)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        pick = [items[i] for i in rng.integers(0, len(items), len(items))]
        # a resampled item can repeat: give each copy its own key so it is counted as many times as drawn
        ans_b = {"%s#%d" % (it, c): ans[it] for c, it in enumerate(pick)}
        boots.append(stats(ans_b, list(ans_b), r0, r1, rounds))

    def ci(get):
        v = [x for x in (get(b) for b in boots) if x is not None]
        return (
            [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
            if len(v) >= max(20, n_boot // 10)
            else None
        )

    cis = {
        k: ci(lambda b, k=k: b[k])
        for k in (
            "tau_ic",
            "tau_ci",
            "p_star_hat",
            "adjacent_tau_ic",
            "adjacent_tau_ci",
            "adjacent_p_star_hat",
            "p1",
            "p_last",
            "delta_rho_debate",
        )
    }
    cis["rho_peer"] = cis["rho_total"] = {
        r: ci(lambda b, r=r: b["rho_peer"][r]) for r in rounds
    }
    cis["k_eff"] = {r: ci(lambda b, r=r: b["k_eff"][r]) for r in rounds}
    tokens = {}
    for r in rounds:
        per_item = [np.mean(tok[it][r]) for it in items if tok[it].get(r)]
        if per_item:
            tokens[r] = float(np.mean(per_item))
    return dict(
        n_items=len(items),
        rounds=rounds,
        first_round=r0,
        last_round=r1,
        n_boot=n_boot,
        point=point,
        ci95=cis,
        mean_tokens_per_call_by_round=tokens or None,
    )


def _f(x, nd=3):
    return "n/a" if x is None else ("%.*f" % (nd, x))


def render(res: dict) -> str:
    p, c = res["point"], res["ci95"]

    def with_ci(key, nd=3):
        return (
            "%s [%s, %s]" % (_f(p[key], nd), _f(c[key][0], nd), _f(c[key][1], nd))
            if c.get(key)
            else _f(p[key], nd)
        )

    out = [
        "Debate dynamics: %d items, rounds %s (first %d to last %d), %d bootstrap resamples over items"
        % (
            res["n_items"],
            res["rounds"],
            res["first_round"],
            res["last_round"],
            res["n_boot"],
        ),
        "flips (item-agent pairs): wrong->right %d, right->wrong %d, right->right %d, wrong->wrong %d"
        % (
            p["wrong_to_right"],
            p["right_to_wrong"],
            p["right_to_right"],
            p["wrong_to_wrong"],
        ),
        "tau_ic (wrong -> right):  " + with_ci("tau_ic"),
        "tau_ci (right -> wrong):  " + with_ci("tau_ci"),
        "p_star_hat = tau_ic / (tau_ic + tau_ci): " + with_ci("p_star_hat"),
        "p1 (first round accuracy): "
        + with_ci("p1")
        + "    p_last: "
        + with_ci("p_last"),
        "delta_rho_debate = rho_total(round %d) - rho_total(round %d): %s"
        % (res["last_round"], res["first_round"], with_ci("delta_rho_debate")),
    ]
    for r in res["rounds"]:
        rc, kc = c["rho_peer"][r], c["k_eff"][r]
        out.append(
            "round %d: rho_total %s%s, K_eff %s%s"
            % (
                r,
                _f(p["rho_peer"][r]),
                " [%s, %s]" % (_f(rc[0]), _f(rc[1])) if rc else "",
                _f(p["k_eff"][r], 2),
                " [%s, %s]" % (_f(kc[0], 2), _f(kc[1], 2)) if kc else "",
            )
        )
    if res["mean_tokens_per_call_by_round"]:
        out.append(
            "mean tokens per call by round: "
            + ", ".join(
                "r%d %.0f" % (r, t)
                for r, t in res["mean_tokens_per_call_by_round"].items()
            )
        )
    else:
        out.append("mean tokens per call by round: n/a (no token fields in the log)")
    if res.get("excess_over_null"):
        ex = res["excess_over_null"]
        out.append(
            "excess over null: adjacent_tau_ic %s, adjacent_tau_ci %s, delta_rho_debate %s"
            % (
                _f(ex.get("excess_adjacent_tau_ic")),
                _f(ex.get("excess_adjacent_tau_ci")),
                _f(ex.get("excess_delta_rho_debate")),
            )
        )
    out.append(
        "rho_total is the correlation of correctness across agents of an item and includes shared item difficulty; delta_rho_debate is its change from the first to the last round, in which shared difficulty largely cancels, so it estimates the correlation added by communication. The tau rates assume the constant-rate model."
    )
    return "\n".join(out)


def peer_transition_table(ans: dict, items: list, rounds: list) -> dict:
    """Compute P(correct at t+1 | own_state_t, n_correct_peers_t) across adjacent rounds."""
    counts = {}
    for it in items:
        agents = ans[it]
        for r_t, r_next in zip(rounds[:-1], rounds[1:]):
            present = [a for a, d in agents.items() if r_t in d and r_next in d]
            if len(present) < 2:
                continue
            n_right_total = sum(agents[a][r_t] for a in present)
            for a in present:
                own = agents[a][r_t]
                n_peers_right = n_right_total - own
                key = (own, n_peers_right)
                c = counts.setdefault(key, [0, 0])
                c[0] += agents[a][r_next]
                c[1] += 1
    return {
        f"own={own},peers_right={pr}": {"p_next": n_ok / tot, "n": tot}
        for (own, pr), (n_ok, tot) in sorted(counts.items())
    }


def excess_over_null(res: dict, null_res: dict) -> dict:
    """Compute excess adjacent transition rates and excess delta_rho_debate over a no-communication null log."""
    p, np_ = res["point"], null_res["point"]

    def _diff(k):
        a, b = p.get(k), np_.get(k)
        return None if (a is None or b is None) else (a - b)

    return {
        "excess_adjacent_tau_ic": _diff("adjacent_tau_ic"),
        "excess_adjacent_tau_ci": _diff("adjacent_tau_ci"),
        "excess_delta_rho_debate": _diff("delta_rho_debate"),
        "null_adjacent_p_star_hat": np_.get("adjacent_p_star_hat"),
        "null_p1": np_.get("p1"),
    }


def influence_diagnostics(path: str, k_agents: int | None = None) -> dict:
    """Load a debate log and attach the Phase 2 peer-influence diagnostics."""
    from .influence import (
        dual_transition_tables,
        fit_influence_models,
        flow_identity_check,
    )

    records = []
    with open(path, encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]
    tables = dual_transition_tables(records)
    if k_agents is None:
        k_agents = len({str(row["agent"]) for row in records if "agent" in row})
    first = [
        row
        for row in records
        if int(row.get("round", -1)) == min(int(item["round"]) for item in records)
    ]
    wrong = sum(not bool(row["correct"]) for row in first)
    right = len(first) - wrong
    transitions = []
    for row in records:
        transitions.append(row)
    by_agent = defaultdict(dict)
    for row in records:
        by_agent[(str(row.get("item")), str(row.get("agent")))][
            int(row.get("round"))
        ] = bool(row.get("correct"))
    fic = fci = 0
    for state in by_agent.values():
        for left, right_state in zip(sorted(state), sorted(state)[1:]):
            fic += int(not state[left] and state[right_state])
            fci += int(state[left] and not state[right_state])
    return {
        "transitions": tables,
        "influence_models": fit_influence_models(tables["by_correct_peers"], k_agents),
        "flow_identity": flow_identity_check(wrong, right, fic, fci),
    }
