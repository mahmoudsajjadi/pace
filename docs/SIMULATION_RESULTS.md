# Estimator simulations (synthetic data)

Produced by `scripts/run_estimator_simulations.py --reps 300 --perms 20 --boot 300`; raw results in `outputs/simulations/estimator_simulations.json`. The data are synthetic and describe the estimators, not any real system. Monte Carlo standard error of a coverage estimate at 300 replicates is about 0.013.

## Study 1: frontier gap (`cme.frontier_gap`)

Planted gap g against the population isotonic self-consistency frontier at the system's mean tokens (population frontier accuracy 0.587). Bias is the mean estimate minus g; coverage is that of the 95% paired bootstrap interval.

| g | N | bias (MC se) | RMSE | coverage | mean width |
|---|---|---|---|---|---|
| -0.05 | 50 | -0.0032 (0.0040) | 0.0692 | 0.973 | 0.310 |
| -0.05 | 250 | -0.0014 (0.0018) | 0.0309 | 0.983 | 0.140 |
| -0.05 | 500 | -0.0010 (0.0013) | 0.0230 | 0.967 | 0.100 |
| -0.05 | 1000 | -0.0010 (0.0009) | 0.0147 | 0.990 | 0.070 |
| +0.00 | 50 | -0.0037 (0.0041) | 0.0708 | 0.973 | 0.306 |
| +0.00 | 250 | -0.0003 (0.0017) | 0.0299 | 0.977 | 0.139 |
| +0.00 | 500 | -0.0018 (0.0013) | 0.0226 | 0.967 | 0.099 |
| +0.00 | 1000 | -0.0000 (0.0009) | 0.0156 | 0.983 | 0.069 |
| +0.05 | 50 | -0.0051 (0.0043) | 0.0738 | 0.953 | 0.301 |
| +0.05 | 250 | -0.0003 (0.0017) | 0.0298 | 0.963 | 0.136 |
| +0.05 | 500 | -0.0025 (0.0013) | 0.0225 | 0.977 | 0.097 |
| +0.05 | 1000 | -0.0004 (0.0009) | 0.0151 | 0.983 | 0.068 |

## Study 2: CR2 intervals (`fit_reml` diagonal, `fit_che` block with the true rho)

True mean -0.2; coverage of the CR2 95% interval for the mean.

| K studies | rho_base | model | coverage | mean width | bias |
|---|---|---|---|---|---|
| 8 | 0.0 | diagonal | 0.953 | 0.243 | -0.0007 |
| 8 | 0.0 | block | 0.953 | 0.243 | -0.0007 |
| 8 | 0.5 | diagonal | 0.940 | 0.263 | +0.0054 |
| 8 | 0.5 | block | 0.930 | 0.261 | +0.0052 |
| 8 | 0.8 | diagonal | 0.957 | 0.269 | -0.0013 |
| 8 | 0.8 | block | 0.947 | 0.267 | -0.0010 |
| 12 | 0.0 | diagonal | 0.953 | 0.187 | -0.0004 |
| 12 | 0.0 | block | 0.953 | 0.187 | -0.0004 |
| 12 | 0.5 | diagonal | 0.943 | 0.203 | -0.0055 |
| 12 | 0.5 | block | 0.943 | 0.202 | -0.0054 |
| 12 | 0.8 | diagonal | 0.967 | 0.215 | +0.0029 |
| 12 | 0.8 | block | 0.963 | 0.214 | +0.0026 |
| 20 | 0.0 | diagonal | 0.963 | 0.141 | +0.0026 |
| 20 | 0.0 | block | 0.963 | 0.141 | +0.0026 |
| 20 | 0.5 | diagonal | 0.950 | 0.154 | +0.0012 |
| 20 | 0.5 | block | 0.947 | 0.153 | +0.0011 |
| 20 | 0.8 | diagonal | 0.953 | 0.158 | -0.0008 |
| 20 | 0.8 | block | 0.957 | 0.157 | -0.0006 |

## Reading

- Frontier gap: the largest absolute bias is 0.0051 (no cell differs from zero by more than two Monte Carlo standard errors); coverage ranges from 0.953 to 0.990, so the interval is at or slightly above nominal for N of 250 and more and is not anti-conservative at N of 50. The settings are one data-generating process with one system shape; they do not show that the estimator is unbiased for every real system.
- CR2: coverage ranges from 0.930 to 0.967 across 8, 12 and 20 clusters and baseline correlations of 0, 0.5 and 0.8. The diagonal and block working models give almost the same coverage and width: the CR2 interval is robust to the working covariance, so the block covariance of Table 5 should be read as a sensitivity check on the point estimate and the variance components, not as a repair of the interval. This study did not examine model-based (Wald) intervals, where the design effect of Proposition A.1 matters most.
