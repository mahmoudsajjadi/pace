"""Closed-form results of Section 3 of the paper, as functions (tested numerically in tests/test_theory_theorems.py).

  manski_upper_bound      Proposition 3.0  (sharp partial-identification bound on the frontier gap)
  telescope               the three-stage telescope identity after Eq. (4)
  hurdle_lambda           Theorem 3.1      (compute-correlation hurdle Lambda)
  coalescence_c / rho_within / k_eff_t    Proposition 3.3 (coalescent collapse under peer imitation)
  disclosure_d            Proposition 3.4  (exponential disclosure bottleneck)
"""
import math
from statistics import NormalDist

N01 = NormalDist()


def manski_upper_bound(p_comm, baseline_accuracies):
    """Upper bound p_comm - max p(pi_0) over the feasible observed baselines; None when there is none (the bound is then vacuous)."""
    vals = list(baseline_accuracies)
    return None if not vals else p_comm - max(vals)


def telescope(p_mas, p_g, p_sc_k, f_sc_ktok):
    """The three brackets [p_SC(K) - p_G], [f_SC(k_tok) - p_SC(K)], [p_MAS - f_SC(k_tok)]; they sum to p_MAS - p_G."""
    return (p_sc_k - p_g, f_sc_ktok - p_sc_k, p_mas - f_sc_ktok)


def z_margin(p):
    return (p - 0.5) / math.sqrt(p * (1 - p))


def k_tok(K, T, r):
    return K * (T + (T - 1) * (K - 1) * r)


def hurdle_lambda(K, T, r, rho_T):
    return math.sqrt((T + (T - 1) * (K - 1) * r) * (1 + (K - 1) * rho_T))


def hurdle_lambda_from_ktok(ktok, K, rho_T):
    """Lambda^2 = k_tok / K_eff, so Lambda = sqrt(k_tok (1 + (K-1) rho_T) / K)."""
    return math.sqrt(ktok * (1 + (K - 1) * rho_T) / K)


def vote_accuracy_normal(p, M_eff):
    """Normal (standardized-margin) approximation to the majority-vote accuracy of M_eff effectively independent answers of accuracy p."""
    return N01.cdf(math.sqrt(M_eff) * z_margin(p))


def debate_clears_frontier(p_T, p_1, K, T, r, rho_T):
    return z_margin(p_T) > z_margin(p_1) * hurdle_lambda(K, T, r, rho_T)


def coalescence_c(gamma, K):
    return 2 * gamma * (1 - gamma) / (K - 1) + (K - 2) * gamma ** 2 / (K - 1) ** 2


def rho_within(t, gamma, K):
    return 1 - (1 - coalescence_c(gamma, K)) ** (t - 1)


def k_eff_t(t, gamma, K):
    return K / (K - (K - 1) * (1 - coalescence_c(gamma, K)) ** (t - 1))


def disclosure_d(q, S):
    return q ** S


def accuracy_from_disclosure(d, a1, a0):
    return d * a1 + (1 - d) * a0
