# mae-eval (prototype)

Compute-accounting and audit utilities for multi-agent LLM evaluations, following `docs/MAEO_SPECIFICATION.md`.

```
pip install -e code/
mae-eval audit --log trace.jsonl --assert-parity --dims r_token,r_sample
```

- The library bundles **no price table**. Pass `--price-in` / `--price-out` (USD per million tokens) or call `ResourceTracker.register_pricing`; otherwise cost is reported as unavailable.
- Trace format (JSON Lines, one call per line): see the docstring of `mae_eval/cli.py`.
- Exit status: 0 success, 1 input error, 2 parity violated (with `--assert-parity`).
