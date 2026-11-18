# mae-eval (prototype)

Compute-accounting and audit utilities for multi-agent LLM evaluations, following `docs/MAEO_SPECIFICATION.md`.

```
pip install -e code/
mae-eval audit --log trace.jsonl --assert-parity --dims r_token,r_sample
```

- The library bundles **no price table**. Pass `--price-in` / `--price-out` (USD per million tokens) or call `ResourceTracker.register_pricing`; otherwise cost is reported as unavailable.
- Trace format (JSON Lines, one call per line): see the docstring of `mae_eval/cli.py`.
- Exit status: 0 success, 1 input error, 2 parity violated (with `--assert-parity`).

## `r_sample` in this legacy tool versus `pace`

`mae-eval` counts the model completions of a run in `r_sample`, so the bundled `code/examples/sample_trace.jsonl` (three parallel workers plus one judge call) reports `r_sample=4`. The `pace` package records `r_sample` as the independent first-round trajectories per item and keeps the number of calls in `r_call`. Compare `r_sample` only between logs written by the same tool.
