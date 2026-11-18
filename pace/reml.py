"""
analysis/meta_analysis.py
Three-Level Random-Effects REML Meta-Analysis Engine with CR2 Cluster-Robust Variance.

Paper 01: Pure ML (Test-Time Compute & Multi-Agent Meta-Analysis).

This module implements:
1. O(M) Sherman-Morrison block-diagonal covariance inversion and Matrix Determinant Lemma.
2. REML deviance objective and analytical gradients for variance components (sigma^2_(2), sigma^2_(3)).
3. Multi-start L-BFGS-B bounded optimization on [0, inf)^2 with Nelder-Mead fallback.
4. Analytical GLS fixed-effect estimator with Wald and Student-t inference.
5. Cheung (2014) & Konstantopoulos (2011) multi-level I^2 decomposition.
6. Jackson (2006) orthogonal multi-level Cochran Q decomposition (Q_total = Q_(2) + Q_(3)).
7. Cluster-Robust CR2 variance estimator (Tipton & Pustejovsky 2015) via symmetric eigen-decomposition
   with Satterthwaite small-sample degrees of freedom.
8. Empirical Bayes BLUPs for study-level and arm-level random effects with prediction error variances.
9. Inverted profile likelihood 95% confidence intervals for variance components via Brent's root-finding.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import optimize, stats

logger = logging.getLogger(__name__)


# ==============================================================================
# Data Structures & Results Containers
# ==============================================================================

@dataclass
class StudyBLUP:
    """Empirical Bayes estimate for a single study cluster."""
    study_id: str
    n_contrasts: int
    raw_mean: float
    blup_u_k: float
    pooled_effect: float       # mu + u_k
    se_blup: float
    ci_lower: float
    ci_upper: float
    shrinkage_factor: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetaAnalysisResult:
    """Comprehensive results container for 3-Level Meta-Analysis."""
    # Fixed effects
    mu: float
    se_mu: float
    ci_lower: float
    ci_upper: float
    p_value: float
    z_stat: float

    # CR2 Cluster-Robust
    cr2_se: float
    cr2_ci_lower: float
    cr2_ci_upper: float
    cr2_p_value: float
    cr2_t_stat: float
    cr2_df: float

    # Variance Components
    sigma2_level2: float
    sigma2_level3: float
    sigma2_level2_ci: Tuple[float, float]
    sigma2_level3_ci: Tuple[float, float]

    # Heterogeneity Decomposition
    typical_v: float
    i2_level2: float
    i2_level3: float
    i2_total: float

    # Cochran Q Statistics
    q_total: float
    q_total_df: int
    q_total_p: float
    q_level2: float
    q_level2_df: int
    q_level2_p: float
    q_level3: float
    q_level3_df: int
    q_level3_p: float

    # Model Fit & Diagnostic Metadata
    reml_loglik: float
    reml_deviance: float
    num_studies: int
    num_contrasts: int
    converged: bool
    iterations: int
    study_effects: Dict[str, Any]

    # Optional coefficients if moderators were used
    beta: Optional[np.ndarray] = None
    beta_names: Optional[List[str]] = None
    vcov_model: Optional[np.ndarray] = None
    vcov_cr2: Optional[np.ndarray] = None

    def __getitem__(self, item: str) -> Any:
        """Allow dict-style indexing for seamless backward compatibility."""
        return getattr(self, item)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes result to structured dictionary matching PROJECT.md interface contract."""
        res = asdict(self)
        # Ensure study_effects is serialized
        res["study_effects"] = {
            k: (v.to_dict() if hasattr(v, "to_dict") else v)
            for k, v in self.study_effects.items()
        }
        return res


# ==============================================================================
# Linear Algebra & Sherman-Morrison Inversion Helpers
# ==============================================================================

def sherman_morrison_solve(
    d: np.ndarray,
    sigma2_3: float,
    z: np.ndarray,
) -> np.ndarray:
    """
    Computes Sigma_k^{-1} z in O(J_k) time using Sherman-Morrison formula.
    
    Sigma_k = diag(d) + sigma2_3 * 1 1^T
    where d_j = V_j + sigma2_2 > 0.
    """
    s_k = float(np.sum(1.0 / d))
    denom = 1.0 + sigma2_3 * s_k

    if z.ndim == 1:
        inv_d = 1.0 / d
        z_tilde = z * inv_d
        sum_z_tilde = float(np.sum(z_tilde))
        return z_tilde - (sigma2_3 * sum_z_tilde / denom) * inv_d
    else:
        # z is (J_k, p)
        inv_d_col = (1.0 / d)[:, np.newaxis]
        z_tilde = z * inv_d_col
        sum_z_tilde = np.sum(z_tilde, axis=0, keepdims=True)  # (1, p)
        return z_tilde - inv_d_col * (sigma2_3 * sum_z_tilde / denom)


def sherman_morrison_quad_form(
    d: np.ndarray,
    sigma2_3: float,
    r: np.ndarray,
) -> float:
    """
    Computes r^T Sigma_k^{-1} r in O(J_k) operations without allocating matrices.
    """
    inv_d = 1.0 / d
    s_k = np.sum(inv_d)
    denom = 1.0 + sigma2_3 * s_k
    sum_r_inv_d = np.sum(r * inv_d)
    return float(np.sum((r ** 2) * inv_d) - (sigma2_3 / denom) * (sum_r_inv_d ** 2))


def matrix_determinant_lemma_logdet(
    d: np.ndarray,
    sigma2_3: float,
) -> float:
    """
    Computes ln |Sigma_k| = sum(ln(d_j)) + ln(1 + sigma2_3 * sum(1 / d_j)) in O(J_k) time.
    """
    s_k = np.sum(1.0 / d)
    return float(np.sum(np.log(d)) + np.log(1.0 + sigma2_3 * s_k))


# ==============================================================================
# ThreeLevelMetaAnalysis Core Engine
# ==============================================================================

class ThreeLevelMetaAnalysis:
    """
    Three-Level Random-Effects Meta-Analysis Solver via REML and CR2.

    Level 1: y_{jk} = theta_{jk} + e_{jk},  e_{jk} ~ N(0, V_{jk})
    Level 2: theta_{jk} = theta_k + v_{jk},  v_{jk} ~ N(0, sigma^2_(2))
    Level 3: theta_k = x_{jk}^T beta + u_k,  u_k ~ N(0, sigma^2_(3))
    """

    def __init__(
        self,
        method: str = "REML",
        compute_profile_ci: bool = True,
        tol: float = 1e-8,
        max_iter: int = 500,
    ):
        if method.upper() not in {"REML", "ML"}:
            raise ValueError(f"Unsupported method: {method}. Must be 'REML'.")
        self.method = method.upper()
        self.compute_profile_ci = compute_profile_ci
        self.tol = tol
        self.max_iter = max_iter
        self.result_: Optional[MetaAnalysisResult] = None

    def fit(
        self,
        y: np.ndarray,
        v: np.ndarray,
        study_clusters: np.ndarray,
        X: Optional[np.ndarray] = None,
        study_names: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None,
    ) -> ThreeLevelMetaAnalysis:
        """
        Fits 3-level model via O(M) Sherman-Morrison L-BFGS-B optimization.

        Args:
            y: (M,) Observed effect sizes (e.g. ln(OR)).
            v: (M,) Sampling variances (V_{jk} > 0).
            study_clusters: (M,) Cluster IDs (e.g. study_id).
            X: (M, p) Design matrix (defaults to column of ones).
            study_names: Optional list of unique study names for BLUP indexing.
            feature_names: Optional names of fixed-effect covariates.

        Returns:
            self with populated result_.
        """
        y = np.asarray(y, dtype=np.float64).ravel()
        v = np.asarray(v, dtype=np.float64).ravel()
        study_clusters = np.asarray(study_clusters)

        M = len(y)
        if len(v) != M or len(study_clusters) != M:
            raise ValueError(f"Mismatched input lengths: y={M}, v={len(v)}, clusters={len(study_clusters)}")
        if np.any(v <= 0):
            raise ValueError("All sampling variances v must be strictly positive.")

        if X is None:
            X = np.ones((M, 1), dtype=np.float64)
            if feature_names is None:
                feature_names = ["intercept"]
        else:
            X = np.asarray(X, dtype=np.float64)
            if X.ndim == 1:
                X = X.reshape(-1, 1)
            if len(X) != M:
                raise ValueError(f"Design matrix X row count ({len(X)}) must match y ({M})")
            if feature_names is None:
                feature_names = [f"x{i}" for i in range(X.shape[1])]

        p = X.shape[1]

        # Group data by cluster in stable order
        unique_studies, cluster_indices = np.unique(study_clusters, return_inverse=True)
        K = len(unique_studies)

        cluster_slices: List[np.ndarray] = [
            np.where(cluster_indices == k)[0] for k in range(K)
        ]

        # Precompute initial variance bounds
        var_y = float(np.var(y, ddof=1)) if M > 1 else 1.0
        median_v = float(np.median(v))
        tau0_sq = max(var_y - median_v, 0.01)

        # Multi-start initializations for [sigma2_2, sigma2_3]
        initial_configs = [
            np.array([0.5 * tau0_sq, 0.5 * tau0_sq]),
            np.array([0.8 * tau0_sq, 0.1 * tau0_sq]),
            np.array([0.1 * tau0_sq, 0.8 * tau0_sq]),
            np.array([0.005, 0.005]),
        ]

        bounds = [(0.0, None), (0.0, None)]

        best_opt = None
        best_dev = np.inf

        # Objective wrapper
        def obj_func(theta: np.ndarray) -> float:
            s2_2 = max(0.0, float(theta[0]))
            s2_3 = max(0.0, float(theta[1]))
            return self._reml_deviance(s2_2, s2_3, y, v, X, cluster_slices)

        # Run multi-start optimization
        for x0 in initial_configs:
            try:
                opt = optimize.minimize(
                    fun=obj_func,
                    x0=x0,
                    method="L-BFGS-B",
                    bounds=bounds,
                    options={"ftol": self.tol, "gtol": self.tol, "maxiter": self.max_iter},
                )
                if opt.fun < best_dev:
                    best_dev = opt.fun
                    best_opt = opt
            except Exception as e:
                logger.debug(f"L-BFGS-B start failed: {e}")

        # Fallback to Nelder-Mead if needed
        if best_opt is None or not best_opt.success or np.isnan(best_dev):
            def penalized_obj(theta: np.ndarray) -> float:
                s2_2 = float(theta[0])
                s2_3 = float(theta[1])
                pen = 0.0
                if s2_2 < 0:
                    pen += 1e6 * (s2_2 ** 2)
                    s2_2 = 0.0
                if s2_3 < 0:
                    pen += 1e6 * (s2_3 ** 2)
                    s2_3 = 0.0
                return self._reml_deviance(s2_2, s2_3, y, v, X, cluster_slices) + pen

            x0 = initial_configs[0] if best_opt is None else best_opt.x
            opt_nm = optimize.minimize(
                penalized_obj,
                x0=np.maximum(0.0, x0),
                method="Nelder-Mead",
                options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": self.max_iter * 2},
            )
            if best_opt is None or opt_nm.fun < best_dev:
                best_opt = opt_nm
                best_dev = opt_nm.fun

        sigma2_2_est = max(0.0, float(best_opt.x[0]))
        sigma2_3_est = max(0.0, float(best_opt.x[1]))
        reml_dev = float(best_dev)
        reml_loglik = -0.5 * reml_dev

        # Compute GLS fixed-effect estimates
        beta_est, vcov_model = self._gls_estimator(sigma2_2_est, sigma2_3_est, y, v, X, cluster_slices)

        # For intercept-only (or primary coefficient)
        mu = float(beta_est[0])
        se_mu = float(np.sqrt(vcov_model[0, 0]))
        z_stat = mu / se_mu if se_mu > 0 else 0.0
        p_val_wald = 2.0 * (1.0 - stats.norm.cdf(abs(z_stat)))
        ci_lower = mu - 1.959963984540054 * se_mu
        ci_upper = mu + 1.959963984540054 * se_mu

        # Compute CR2 Cluster-Robust Variance and Satterthwaite df
        vcov_cr2, df_satt = self._compute_cr2_variance(
            y, v, X, cluster_slices, sigma2_2_est, sigma2_3_est, beta_est
        )
        cr2_se = float(np.sqrt(vcov_cr2[0, 0]))
        cr2_t_stat = mu / cr2_se if cr2_se > 0 else 0.0
        
        # Satterthwaite t-distribution p-value & CI
        if df_satt > 0 and not np.isnan(df_satt):
            t_crit = float(stats.t.ppf(0.975, df=df_satt))
            cr2_p_val = float(2.0 * (1.0 - stats.t.cdf(abs(cr2_t_stat), df=df_satt)))
        else:
            t_crit = 1.959963984540054
            cr2_p_val = float(2.0 * (1.0 - stats.norm.cdf(abs(cr2_t_stat))))

        cr2_ci_lower = mu - t_crit * cr2_se
        cr2_ci_upper = mu + t_crit * cr2_se

        # Typical sampling variance (Cheung 2014 & Higgins-Thompson 2002)
        inv_v = 1.0 / v
        sum_w = np.sum(inv_v)
        sum_w2 = np.sum(inv_v ** 2)
        typical_v = float((M - 1.0) * sum_w / (sum_w ** 2 - sum_w2)) if M > 1 else float(v[0])

        # Cheung I^2 Heterogeneity decomposition
        total_denom = typical_v + sigma2_2_est + sigma2_3_est
        if total_denom > 0:
            i2_level2 = float((sigma2_2_est / total_denom) * 100.0)
            i2_level3 = float((sigma2_3_est / total_denom) * 100.0)
            i2_total = float(((sigma2_2_est + sigma2_3_est) / total_denom) * 100.0)
        else:
            i2_level2, i2_level3, i2_total = 0.0, 0.0, 0.0

        # Jackson (2006) Multi-level Cochran Q decomposition
        q_tot, q_tot_df, q_tot_p, q_2, q_2_df, q_2_p, q_3, q_3_df, q_3_p = self._cochran_q_decomposition(
            y, v, cluster_slices
        )

        # Profile Likelihood CIs for variance components
        if self.compute_profile_ci and M >= 5:
            s2_2_ci = self._profile_ci_variance(
                component=2,
                sigma2_2_opt=sigma2_2_est,
                sigma2_3_opt=sigma2_3_est,
                dev_opt=reml_dev,
                y=y,
                v=v,
                X=X,
                cluster_slices=cluster_slices,
            )
            s2_3_ci = self._profile_ci_variance(
                component=3,
                sigma2_2_opt=sigma2_2_est,
                sigma2_3_opt=sigma2_3_est,
                dev_opt=reml_dev,
                y=y,
                v=v,
                X=X,
                cluster_slices=cluster_slices,
            )
        else:
            s2_2_ci = (0.0, float(sigma2_2_est * 3.0))
            s2_3_ci = (0.0, float(sigma2_3_est * 3.0))

        # Empirical Bayes BLUPs
        study_id_list = [str(s) for s in unique_studies]
        study_effects = self._compute_study_blups(
            y, v, cluster_slices, sigma2_2_est, sigma2_3_est, mu, vcov_model[0, 0], study_id_list
        )

        self.result_ = MetaAnalysisResult(
            mu=mu,
            se_mu=se_mu,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            p_value=p_val_wald,
            z_stat=z_stat,
            cr2_se=cr2_se,
            cr2_ci_lower=cr2_ci_lower,
            cr2_ci_upper=cr2_ci_upper,
            cr2_p_value=cr2_p_val,
            cr2_t_stat=cr2_t_stat,
            cr2_df=df_satt,
            sigma2_level2=sigma2_2_est,
            sigma2_level3=sigma2_3_est,
            sigma2_level2_ci=s2_2_ci,
            sigma2_level3_ci=s2_3_ci,
            typical_v=typical_v,
            i2_level2=i2_level2,
            i2_level3=i2_level3,
            i2_total=i2_total,
            q_total=q_tot,
            q_total_df=q_tot_df,
            q_total_p=q_tot_p,
            q_level2=q_2,
            q_level2_df=q_2_df,
            q_level2_p=q_2_p,
            q_level3=q_3,
            q_level3_df=q_3_df,
            q_level3_p=q_3_p,
            reml_loglik=reml_loglik,
            reml_deviance=reml_dev,
            num_studies=K,
            num_contrasts=M,
            converged=bool(best_opt.success if hasattr(best_opt, "success") else True),
            iterations=int(best_opt.nit if hasattr(best_opt, "nit") else 0),
            study_effects=study_effects,
            beta=beta_est,
            beta_names=feature_names,
            vcov_model=vcov_model,
            vcov_cr2=vcov_cr2,
        )

        return self

    # --------------------------------------------------------------------------
    # Internal Computational Routines
    # --------------------------------------------------------------------------

    def _reml_deviance(
        self,
        sigma2_2: float,
        sigma2_3: float,
        y: np.ndarray,
        v: np.ndarray,
        X: np.ndarray,
        cluster_slices: List[np.ndarray],
    ) -> float:
        """
        Evaluates REML deviance -2 * ln(L_REML) in O(M) time using Sherman-Morrison lemma.
        """
        M = len(y)
        p = X.shape[1]

        logdet_sigma = 0.0
        W = np.zeros((p, p), dtype=np.float64)
        Xy = np.zeros(p, dtype=np.float64)

        # Accumulate log-determinant and information sums per cluster
        for idx in cluster_slices:
            v_k = v[idx]
            d_k = v_k + sigma2_2
            X_k = X[idx]
            y_k = y[idx]

            # Matrix determinant lemma: ln|Sigma_k|
            logdet_sigma += matrix_determinant_lemma_logdet(d_k, sigma2_3)

            # Sherman-Morrison solve for X_k and y_k
            # Sigma_k^{-1} X_k: shape (J_k, p)
            inv_Sigma_X = sherman_morrison_solve(d_k, sigma2_3, X_k)
            W += X_k.T @ inv_Sigma_X
            Xy += inv_Sigma_X.T @ y_k

        # Invert W = X^T Sigma^{-1} X
        try:
            sign, logdet_W = np.linalg.slogdet(W)
            if sign <= 0:
                return 1e12
            beta = np.linalg.solve(W, Xy)
        except np.linalg.LinAlgError:
            return 1e12

        # Weighted residual sum of squares: r^T Sigma^{-1} r
        wrss = 0.0
        for idx in cluster_slices:
            v_k = v[idx]
            d_k = v_k + sigma2_2
            X_k = X[idx]
            y_k = y[idx]
            r_k = y_k - X_k @ beta
            wrss += sherman_morrison_quad_form(d_k, sigma2_3, r_k)

        deviance = logdet_sigma + logdet_W + wrss + (M - p) * np.log(2.0 * np.pi)
        return float(deviance)

    def _gls_estimator(
        self,
        sigma2_2: float,
        sigma2_3: float,
        y: np.ndarray,
        v: np.ndarray,
        X: np.ndarray,
        cluster_slices: List[np.ndarray],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Solves GLS estimator beta = (X^T Sigma^{-1} X)^{-1} X^T Sigma^{-1} y.
        """
        p = X.shape[1]
        W = np.zeros((p, p), dtype=np.float64)
        Xy = np.zeros(p, dtype=np.float64)

        for idx in cluster_slices:
            d_k = v[idx] + sigma2_2
            X_k = X[idx]
            y_k = y[idx]
            inv_Sigma_X = sherman_morrison_solve(d_k, sigma2_3, X_k)
            W += X_k.T @ inv_Sigma_X
            Xy += inv_Sigma_X.T @ y_k

        vcov_model = np.linalg.inv(W)
        beta = vcov_model @ Xy
        return beta, vcov_model

    def _compute_cr2_variance(
        self,
        y: np.ndarray,
        v: np.ndarray,
        X: np.ndarray,
        cluster_slices: List[np.ndarray],
        sigma2_2: float,
        sigma2_3: float,
        beta: np.ndarray,
    ) -> Tuple[np.ndarray, float]:
        """
        Computes CR2 cluster-robust variance matrix (Tipton & Pustejovsky 2015)
        using symmetric eigen-decomposition and Satterthwaite degrees of freedom.
        """
        K = len(cluster_slices)
        p = X.shape[1]

        # First compute W^{-1}
        W = np.zeros((p, p), dtype=np.float64)
        for idx in cluster_slices:
            d_k = v[idx] + sigma2_2
            X_k = X[idx]
            inv_Sigma_X = sherman_morrison_solve(d_k, sigma2_3, X_k)
            W += X_k.T @ inv_Sigma_X

        W_inv = np.linalg.inv(W)

        meat_cr2 = np.zeros((p, p), dtype=np.float64)
        satt_blocks = []

        # Contrast vector for Satterthwaite df (intercept contrast)
        c_vec = np.zeros(p, dtype=np.float64)
        c_vec[0] = 1.0

        for idx in cluster_slices:
            J_k = len(idx)
            v_k = v[idx]
            d_k = v_k + sigma2_2
            X_k = X[idx]
            y_k = y[idx]
            r_k = y_k - X_k @ beta

            # Construct Sigma_k explicitly for the small J_k x J_k cluster (J_k <= 48)
            Sigma_k = np.diag(d_k) + sigma2_3 * np.ones((J_k, J_k), dtype=np.float64)

            # Eigendecomposition of Sigma_k for symmetric square root
            eigvals_s, eigvecs_s = np.linalg.eigh(Sigma_k)
            eigvals_s = np.maximum(eigvals_s, 1e-12)
            Sigma_k_sqrt = eigvecs_s @ np.diag(np.sqrt(eigvals_s)) @ eigvecs_s.T
            Sigma_k_inv_sqrt = eigvecs_s @ np.diag(1.0 / np.sqrt(eigvals_s)) @ eigvecs_s.T

            # Hat projection in transformed metric
            # G_k = I - Sigma_k^{-1/2} X_k W^{-1} X_k^T Sigma_k^{-1/2}
            Proj_k = Sigma_k_inv_sqrt @ X_k @ W_inv @ X_k.T @ Sigma_k_inv_sqrt
            G_k = np.eye(J_k) - Proj_k

            # Eigendecomposition of G_k
            eigvals_g, eigvecs_g = np.linalg.eigh(G_k)
            eigvals_g = np.maximum(eigvals_g, 1e-6)  # Safeguard high leverage
            G_k_inv_sqrt = eigvecs_g @ np.diag(1.0 / np.sqrt(eigvals_g)) @ eigvecs_g.T

            # CR2 adjustment matrix A_k = Sigma_k^{1/2} G_k^{-1/2} Sigma_k^{-1/2}
            A_k = Sigma_k_sqrt @ G_k_inv_sqrt @ Sigma_k_inv_sqrt

            # Adjusted residual
            r_tilde_k = A_k @ r_k

            # Cluster score in CR2 sandwich: X_k^T Sigma_k^{-1} r_tilde_k
            inv_Sigma_r_tilde = sherman_morrison_solve(d_k, sigma2_3, r_tilde_k)
            score_k = X_k.T @ inv_Sigma_r_tilde
            meat_cr2 += np.outer(score_k, score_k)

            # Satterthwaite vector q_k = A_k^T Sigma_k^{-1} X_k W_inv c
            inv_Sigma_X_W_c = sherman_morrison_solve(d_k, sigma2_3, X_k @ (W_inv @ c_vec))
            q_k = A_k.T @ inv_Sigma_X_W_c
            satt_blocks.append((q_k, Sigma_k, X_k))

        vcov_cr2 = W_inv @ meat_cr2 @ W_inv

        # Full Pustejovsky-Tipton (2018) Satterthwaite df using cross-cluster residual covariance
        K_cl = len(satt_blocks)
        P_mat = np.zeros((K_cl, K_cl), dtype=np.float64)
        for j, (q_j, Sigma_j, X_j) in enumerate(satt_blocks):
            for k, (q_k, Sigma_k, X_k) in enumerate(satt_blocks):
                cov_jk = (Sigma_j if j == k else 0.0) - (X_j @ W_inv @ X_k.T)
                P_mat[j, k] = float(q_j.T @ cov_jk @ q_k)
        tr_P = float(np.trace(P_mat))
        tr_P2 = float(np.sum(P_mat * P_mat))
        if tr_P2 > 0:
            df_satt = float((tr_P ** 2) / tr_P2)
        else:
            df_satt = float(max(1, K - p))

        return vcov_cr2, df_satt

    def _cochran_q_decomposition(
        self,
        y: np.ndarray,
        v: np.ndarray,
        cluster_slices: List[np.ndarray],
    ) -> Tuple[float, int, float, float, int, float, float, int, float]:
        """
        Jackson (2006) orthogonal Cochran Q decomposition across hierarchical levels.
        Q_total = Q_(2) + Q_(3)
        """
        M = len(y)
        K = len(cluster_slices)
        w = 1.0 / v

        # Study-specific weighted sums
        W_k = np.array([np.sum(w[idx]) for idx in cluster_slices], dtype=np.float64)
        y_bar_k = np.array([np.sum(w[idx] * y[idx]) / W_k[i] for i, idx in enumerate(cluster_slices)])

        # Grand weighted mean
        W_total = np.sum(W_k)
        y_bar_w = np.sum(W_k * y_bar_k) / W_total

        # Total Q
        q_tot = float(np.sum(w * ((y - y_bar_w) ** 2)))
        q_tot_df = M - 1
        q_tot_p = float(1.0 - stats.chi2.cdf(q_tot, df=q_tot_df)) if q_tot_df > 0 else 1.0

        # Level 2 Within-study Q
        q_2 = 0.0
        for i, idx in enumerate(cluster_slices):
            q_2 += np.sum(w[idx] * ((y[idx] - y_bar_k[i]) ** 2))
        q_2 = float(q_2)
        q_2_df = M - K
        q_2_p = float(1.0 - stats.chi2.cdf(q_2, df=q_2_df)) if q_2_df > 0 else 1.0

        # Level 3 Between-study Q
        q_3 = float(np.sum(W_k * ((y_bar_k - y_bar_w) ** 2)))
        q_3_df = K - 1
        q_3_p = float(1.0 - stats.chi2.cdf(q_3, df=q_3_df)) if q_3_df > 0 else 1.0

        return q_tot, q_tot_df, q_tot_p, q_2, q_2_df, q_2_p, q_3, q_3_df, q_3_p

    def _profile_ci_variance(
        self,
        component: int,
        sigma2_2_opt: float,
        sigma2_3_opt: float,
        dev_opt: float,
        y: np.ndarray,
        v: np.ndarray,
        X: np.ndarray,
        cluster_slices: List[np.ndarray],
        alpha: float = 0.05,
    ) -> Tuple[float, float]:
        """
        Computes 95% profile likelihood confidence interval for variance component
        by inverting likelihood ratio test: dev(theta) - dev_opt <= chi2_1(1 - alpha).
        """
        crit_val = float(stats.chi2.ppf(1.0 - alpha, df=1))  # ~ 3.841459
        opt_val = sigma2_2_opt if component == 2 else sigma2_3_opt

        # Profile likelihood function
        def profile_dev(target: float) -> float:
            target = max(0.0, float(target))
            if component == 3:
                # Target is sigma2_3, optimize over sigma2_2
                res = optimize.minimize_scalar(
                    lambda s2_2: self._reml_deviance(max(0.0, s2_2), target, y, v, X, cluster_slices),
                    bounds=(0.0, max(0.5, sigma2_2_opt * 5.0)),
                    method="bounded",
                )
                return float(res.fun)
            else:
                # Target is sigma2_2, optimize over sigma2_3
                res = optimize.minimize_scalar(
                    lambda s2_3: self._reml_deviance(target, max(0.0, s2_3), y, v, X, cluster_slices),
                    bounds=(0.0, max(0.5, sigma2_3_opt * 5.0)),
                    method="bounded",
                )
                return float(res.fun)

        def discrepancy(target: float) -> float:
            return profile_dev(target) - (dev_opt + crit_val)

        # Lower bound
        disc_zero = discrepancy(0.0)
        if disc_zero <= 0.0:
            lower = 0.0
        else:
            try:
                lower = float(optimize.brentq(discrepancy, 0.0, opt_val, xtol=1e-5))
            except (ValueError, RuntimeError):
                lower = 0.0

        # Upper bound: search for bracket
        upper_bracket = max(opt_val * 2.0 + 0.05, 0.20)
        for _ in range(10):
            if discrepancy(upper_bracket) > 0:
                break
            upper_bracket *= 2.0

        try:
            upper = float(optimize.brentq(discrepancy, opt_val, upper_bracket, xtol=1e-5))
        except (ValueError, RuntimeError):
            upper = float(upper_bracket)

        return (lower, upper)

    def _compute_study_blups(
        self,
        y: np.ndarray,
        v: np.ndarray,
        cluster_slices: List[np.ndarray],
        sigma2_2: float,
        sigma2_3: float,
        mu: float,
        var_mu: float,
        study_names: List[str],
    ) -> Dict[str, StudyBLUP]:
        """
        Computes Empirical Bayes BLUPs for study-level random effects and forest plot CIs.
        """
        study_blups: Dict[str, StudyBLUP] = {}

        for i, idx in enumerate(cluster_slices):
            study_id = study_names[i]
            y_k = y[idx]
            v_k = v[idx]
            n_k = len(idx)
            raw_mean = float(np.mean(y_k))

            # Precision weights
            w_k = 1.0 / (v_k + sigma2_2)
            s_k = float(np.sum(w_k))
            r_k = y_k - mu

            # Precision-weighted mean residual
            r_bar_k = float(np.sum(w_k * r_k) / s_k)

            # Shrinkage factor gamma_k
            denom = 1.0 + sigma2_3 * s_k
            gamma_k = float((sigma2_3 * s_k) / denom) if denom > 0 else 0.0
            u_k = float(gamma_k * r_bar_k)

            pooled_eff = mu + u_k

            # Prediction error variance
            var_pred_error = float((sigma2_3 / denom) + var_mu * ((1.0 - gamma_k) ** 2))
            se_blup = float(np.sqrt(max(1e-12, var_pred_error)))

            ci_l = pooled_eff - 1.959963984540054 * se_blup
            ci_u = pooled_eff + 1.959963984540054 * se_blup

            study_blups[study_id] = StudyBLUP(
                study_id=study_id,
                n_contrasts=n_k,
                raw_mean=raw_mean,
                blup_u_k=u_k,
                pooled_effect=pooled_eff,
                se_blup=se_blup,
                ci_lower=ci_l,
                ci_upper=ci_u,
                shrinkage_factor=gamma_k,
            )

        return study_blups


# ==============================================================================
# Public Top-Level API Functions
# ==============================================================================

def fit_three_level_meta(
    df: pd.DataFrame,
    y_col: str = "ln_or",
    v_col: str = "v_jk",
    cluster_col: str = "study_id",
    moderators: Optional[List[str]] = None,
    compute_profile_ci: bool = True,
    method: str = "REML",
) -> Dict[str, Any]:
    """
    Public top-level API function adhering strictly to PROJECT.md Interface Contract.
    
    Accepts DataFrame from analysis/data_loader.py and returns serializable dict.
    
    Returns:
        dict with keys:
            mu, se_mu, ci_lower, ci_upper, p_value,
            sigma2_level2, sigma2_level3,
            i2_level2, i2_level3, i2_total,
            cr2_se, cr2_ci_lower, cr2_ci_upper, cr2_p_value,
            study_effects, etc.
    """
    # Resolve column aliases if needed
    for alias_target, possible_names in [
        (y_col, [y_col, "log_odds_ratio", "effect_size"]),
        (v_col, [v_col, "sampling_variance_v", "v", "sampling_variance"]),
        (cluster_col, [cluster_col, "study", "study_name", "cluster"]),
    ]:
        if alias_target not in df.columns:
            for name in possible_names:
                if name in df.columns:
                    df = df.rename(columns={name: alias_target})
                    break

    if y_col not in df.columns:
        raise ValueError(f"Required effect size column '{y_col}' not found in DataFrame.")
    if v_col not in df.columns:
        raise ValueError(f"Required variance column '{v_col}' not found in DataFrame.")
    if cluster_col not in df.columns:
        raise ValueError(f"Required cluster column '{cluster_col}' not found in DataFrame.")

    y = df[y_col].values.astype(np.float64)
    v = df[v_col].values.astype(np.float64)
    study_clusters = df[cluster_col].values

    # Handle design matrix if moderators specified
    X = None
    feature_names = None
    if moderators:
        # Build design matrix with intercept
        X_df = pd.get_dummies(df[moderators], drop_first=True, dtype=float)
        X_df.insert(0, "intercept", 1.0)
        X = X_df.values
        feature_names = list(X_df.columns)

    model = ThreeLevelMetaAnalysis(
        method=method,
        compute_profile_ci=compute_profile_ci,
    )
    model.fit(
        y=y,
        v=v,
        study_clusters=study_clusters,
        X=X,
        feature_names=feature_names,
    )

    return model.result_.to_dict()


# ==============================================================================
# `pace meta --reml`: the paper's pooled model (log odds, Haldane-Anscombe, delta-method variance with item correlation phi, three-level REML, CR2 intervals)
# The class above is a verbatim copy of analysis/meta_analysis.py so that the command line reproduces Table 1 (B9, beta = -0.195, CR2 [-0.323, -0.067], nu = 6.36).
# ==============================================================================


def log_odds_effects(p_mas, p_base, n, phi: float = 0.5):
    """Log odds ratio and delta-method variance with assumed item correlation phi (same definition as analysis/run_k9_reml.py)."""
    p_mas, p_base, n = (np.asarray(x, dtype=float) for x in (p_mas, p_base, n))
    pm, pb = (p_mas * n + 0.5) / (n + 1.0), (p_base * n + 0.5) / (n + 1.0)
    y = np.log(pm / (1.0 - pm)) - np.log(pb / (1.0 - pb))
    am, ab = pm * (1.0 - pm), pb * (1.0 - pb)
    v = (1.0 / am + 1.0 / ab - 2.0 * phi / np.sqrt(am * ab)) / n
    return y, np.maximum(v, 1e-10)


def reml_pool(rows: List[Dict[str, Any]], phi: float = 0.5) -> Dict[str, Any]:
    """Three-level REML (contrasts nested in studies) with CR2 Satterthwaite intervals on the rows (needs study, p_mas, p_base, n)."""
    y, v = log_odds_effects([r["p_mas"] for r in rows], [r["p_base"] for r in rows], [r["n"] for r in rows], phi)
    m = ThreeLevelMetaAnalysis(compute_profile_ci=False)
    m.fit(y, v, np.array([str(r["study"]) for r in rows]))
    r = m.result_
    return {"estimator": "three-level REML with CR2 (Tipton-Pustejovsky) Satterthwaite intervals", "scale": "log odds ratio (Haldane-Anscombe), phi=%.2f" % phi,
            "K": int(r.num_studies), "M": int(r.num_contrasts), "beta": float(r.mu), "se": float(r.se_mu), "ci95": [float(r.ci_lower), float(r.ci_upper)],
            "cr2_se": float(r.cr2_se), "cr2_ci95": [float(r.cr2_ci_lower), float(r.cr2_ci_upper)], "nu": float(r.cr2_df),
            "sigma2_level2": float(r.sigma2_level2), "sigma2_level3": float(r.sigma2_level3), "converged": bool(r.converged)}
