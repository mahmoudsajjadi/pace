"""Power audit of published multi-agent gains (addendum N1; exploratory, not part of the frozen v1 numbers).

For a paired comparison of two accuracies on the same n items, the standard error of the accuracy difference is
  se = sqrt((p1(1-p1) + p2(1-p2) - 2 phi sqrt(p1(1-p1) p2(1-p2))) / n),
with phi the correlation of the two arms' item outcomes (the same phi used by `pace power` and the noise band). The minimum detectable effect (MDE) at two-sided level alpha and power
1 - beta is (z_{1-alpha/2} + z_{1-beta}) * se, evaluated under the null p2 = p1 = p_base (the benchmark size, not the observed gain, fixes the MDE). A gain smaller than its own MDE could
not have been reliably detected at that benchmark size.
"""
import csv
import math
from statistics import NormalDist

N01 = NormalDist()


def paired_se(p1, p2, n, phi):
    v = p1 * (1 - p1) + p2 * (1 - p2) - 2 * phi * math.sqrt(p1 * (1 - p1) * p2 * (1 - p2))
    return math.sqrt(max(v, 0.0) / n)


def mde(p_base, n, phi=0.5, alpha=0.05, power=0.8):
    if not 0 < p_base < 1 or n <= 0:
        return None
    return (N01.inv_cdf(1 - alpha / 2) + N01.inv_cdf(power)) * paired_se(p_base, p_base, n, phi)


def audit_ledger(rows, phis=(0.3, 0.5, 0.7), alpha=0.05, power=0.8):
    """rows: dicts with study, category, key, d, p_base, n. Returns summary per phi."""
    clean = []
    for r in rows:
        try:
            clean.append({"cat": r["category"], "key": r["key"], "d": float(r["d"]), "p": float(r["p_base"]), "n": float(r["n"]), "study": r.get("study", "")})
        except (KeyError, ValueError, TypeError):
            continue
    bc_by_key = {}
    for r in clean:
        if r["cat"] in ("B", "C"):
            bc_by_key.setdefault(r["key"], []).append(r)
    out = {}
    for phi in phis:
        a_gain = [r for r in clean if r["cat"] == "A" and r["d"] > 0 and mde(r["p"], r["n"], phi, alpha, power) is not None]
        below = [r for r in a_gain if r["d"] < mde(r["p"], r["n"], phi, alpha, power)]
        survive_pos = [r for r in a_gain if any(b["d"] > 0 for b in bc_by_key.get(r["key"], []))]
        survive_det = [r for r in a_gain if any(b["d"] >= mde(b["p"], b["n"], phi, alpha, power) for b in bc_by_key.get(r["key"], []) if mde(b["p"], b["n"], phi, alpha, power))]
        with_bc = [r for r in a_gain if r["key"] in bc_by_key]
        mdes = sorted(mde(r["p"], r["n"], phi, alpha, power) for r in clean if r["cat"] == "A" and mde(r["p"], r["n"], phi, alpha, power) is not None)
        out[str(phi)] = {"phi": phi, "n_A_gains": len(a_gain), "n_below_own_mde": len(below),
                         "share_below_own_mde": len(below) / len(a_gain) if a_gain else None,
                         "n_with_BC_counterpart": len(with_bc), "n_still_positive_in_BC": len(survive_pos), "n_still_detectable_in_BC": len(survive_det),
                         "median_mde_A": mdes[len(mdes) // 2] if mdes else None}
    return out


def read_ledger(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))
