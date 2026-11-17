# Master Execution Specification for Claude: CME Reusable Research Infrastructure & Empirical Protocol

**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Affiliation:** Department of Computer Science and Engineering, University of Nevada, Reno  
**Contact:** `mahmoud.sajjadi@unr.edu`  
**Repository Path:** `c:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute`  
**Document Purpose:** Drop-in Master Specification for Claude Code to execute all research, software engineering, evaluation, and documentation phases.

---

## 1. Executive Directive & Strategic Pivot

### Core Directive:
> **Do NOT build the plan around obtaining official conference endorsement, making the checklist mandatory, or projecting speculative citation compounding (e.g., "6,000+ citations"). Build a reusable research object that independent researchers actively choose to use because it makes their multi-agent and reasoning experiments easier to design, compare, audit, and reproduce.**

### Lessons from High-Uptake 2025 Literature:
- **OpenHands, Qwen3, DeepSeek-R1, and DAPO** succeeded by giving the community **something functional to run**, a clear training/evaluation harness, and reproducible datasets.
- **The Illusion of Thinking & Snell et al.** succeeded by asking a sharp, testable question: *"Are we measuring reasoning, or did we just give one method more compute?"*
- Checklists (like Pineau et al. or Dodge et al.) succeed only when they are easy to run, non-punitive, and supported by usable software tools.

---

## 2. The 3-Component Architecture of CME

CME is structured into three connected components:

1. **Component A: Resource-Accounting Specification (`docs/RESOURCE_ACCOUNTING_SCHEMA.md`)**
   - A versioned, machine-readable JSON schema recording exact resource usage at both the **individual model-call level** and the **complete run level**.
   - Strict provenance: Every metric is explicitly tagged as `measured`, `estimated`, or `unavailable`. Estimates are never represented as physical measurements.
   - Accurately captures concurrency: Distinguishes serialized critical-path latency ($R_{\text{lat}}$) from the arithmetic sum of call latencies, and isolates productive reasoning tokens ($R_{\text{reason}}$) from prompt repetition/scaffold overhead ($R_{\text{scaffold}}$).
   - Harmonized with the October 2026 IETF Internet-Draft *"Agent Run Metrics"*.

2. **Component B: Fair-Comparison Protocol & Pareto Framework (`docs/CME_METHOD_SPEC.md`)**
   - Rules for comparing single-agent, multi-agent, sampling, and reasoning strategies under explicitly declared constraints.
   - Disentangles the independent dimensions of test-time scaling:
     * Equal generated tokens
     * Equal total monetary cost
     * Equal serialized latency
     * Equal independent samples
     * Equal model forward calls
   - Mandatory strong single-agent baselines: Prohibits comparisons against single greedy calls ($K=1, T=0.0$) when multi-agent systems use multiple samples or expanded tokens. Requires comparison against Self-Consistency (CoT-SC), Best-of-$N$, or budget-matched thinking tokens.
   - Evaluates performance along the **performance-resource Pareto frontier**.

3. **Component C: Executable Evaluation Toolkit (`code/mae_eval`)**
   - Zero-dependency, pip-installable Python package (`pip install -e code/`).
   - Clean CLI: `mae-eval audit`, `mae-eval validate`, `mae-eval checklist`.
   - Generates reproducible Markdown, JSON, and publication-ready LaTeX tables.

---

## 3. Manuscript Enhancements: Influential Papers & Positioning

### 3.1 Positioning Statement (Insert into Section 2 Related Work)
In `manuscript/section2_related_work.tex`, position CME clearly with this exact statement:
> *"Existing evaluation frameworks have advanced benchmark coverage, reproducibility, and reasoning assessment. However, a unified, executable approach to distinguishing coordination gains from additional sampling and inference-resource expenditure remains an important methodological challenge."*

### 3.2 Influential Papers & Reusable Contributions Table (Insert into Manuscript Section 2)
Add the following comparative benchmark table into `manuscript/section2_related_work.tex` (and `tables/table_influential_frameworks.tex`):

```latex
\begin{table*}[t!]
\centering
\small
\caption{\textbf{Influential Evaluation Frameworks and Reusable Methodological Contributions.} Comparison of milestone evaluation and test-time reasoning papers, their core contributions, why they achieved community uptake, and their direct methodological lessons for Compute-Matched Evaluation (CME).}
\label{tab:influential_frameworks}
\begin{tabularx}{\textwidth}{l p{3.2cm} p{5.2cm} X}
\toprule
\textbf{Paper / Framework} & \textbf{Main Contribution} & \textbf{Why It Became Influential} & \textbf{Methodological Lesson for CME} \\
\midrule
Chain-of-Thought \citep{wei2022chain} & Step-by-step reasoning prompting & Simple, zero-training reusable prompt format & Provide a transparent, low-friction experimental protocol. \\
\addlinespace[2pt]
Self-Consistency \citep{wang2022selfconsistency} & Stochastic sampling and majority voting & Strong baseline that resolved greedy decoding fragility & Make independent sample-matched baselines (CoT-SC) mandatory. \\
\addlinespace[2pt]
HELM \citep{liang2022holistic} & Holistic evaluation framework & Modular, executable benchmark harness across models & Release open executable tools and standardized telemetry schemas. \\
\addlinespace[2pt]
Reproducibility Checklist \citep{pineau2021improving} & Research reporting standards & Low-friction reporting rubric integrated into peer review & Focus on transparent resource accounting rather than punitive bans. \\
\addlinespace[2pt]
The Illusion of Thinking \citep{illusion2025} & Reasoning capability evaluation & Focused, provocative question on test-time scaling limits & Frame central empirical questions crisply (coordination vs compute). \\
\addlinespace[2pt]
DeepSeek-R1 \citep{deepseek2025r1} & Open reasoning model and RL recipe & Fully open weights, execution traces, and distillations & Ground evaluation standards in verifiable, open-weights experimentation. \\
\addlinespace[2pt]
DAPO \citep{dapo2025} & Open-source scalable RL system & Complete method, training code, and curated datasets & Provide a working, reproducible Python implementation. \\
\addlinespace[2pt]
OpenHands \citep{wang2025openhands} & Open agent software platform & Modular software infrastructure across 13 diverse benchmarks & Build an extensible evaluation library (`mae-eval`) for the community. \\
\bottomrule
\end{tabularx}
\end{table*}
```

*(Note: Raw citation count comparison tables belong in internal strategic reports such as `docs/CITATION_ADOPTION_EVIDENCE_2025_2026.md`, NOT in the scientific manuscript text).*

---

## 4. Phase-by-Phase Claude Execution Roadmap

Execute the following 10 phases sequentially:

### Phase 1: Environment & Implementation Audit
- Verify package installation: `python -m pip install -e code/`.
- Verify CLI entry points via subprocess without manual environment hacks:
  * `mae-eval --help` (exit code 0).
  * `mae-eval checklist --format markdown` (exit code 0).
  * `mae-eval checklist --format latex` (exit code 0).
  * `mae-eval checklist --format json` (exit code 0).
- Run full test suite: `pytest tests/ -v`. Ensure 100% pass rate.
- Run `python analysis/assemble_paper.py`. Verify `main.pdf` and `tmlr_submission.pdf` compile with 0 errors and 0 undefined references.

### Phase 2: Evidence-Based Citation & Adoption Research
- Review `docs/CITATION_ADOPTION_EVIDENCE_2025_2026.md`.
- Ensure all 2025 case studies (Qwen3, DeepSeek-R1, DAPO, OpenHands, The Illusion of Thinking, Snell et al., Yang et al.) have verified retrieval dates, database discrepancies (Semantic Scholar vs OpenAlex), and citing mode classifications.
- Maintain the section: *"What a Solo-Author Evaluation Paper Can Realistically Learn"*.

### Phase 3: Rebuild the CME Scientific Contribution
- Review `docs/CME_METHOD_SPEC.md`.
- Ensure the three connected components (Resource-Accounting Specification, Fair-Comparison Protocol, Executable Evaluation Toolkit) are operationalized.
- Clarify definitions: Resource Measurement vs. Budget Matching vs. Coordination Attribution vs. Pareto Trade-offs vs. Deployment Heuristics.

### Phase 4: Resource-Accounting Schema & Validator Implementation
- Review `docs/RESOURCE_ACCOUNTING_SCHEMA.md`.
- In `code/mae_eval/`:
  * Implement `code/mae_eval/schema.py` defining JSON Schemas for `CallRecord` and `RunManifest`.
  * Add validation function `validate_record(data: dict) -> Tuple[bool, List[str]]`.
  * Enforce strict provenance (`measured`, `estimated`, `unavailable`).
  * Add CLI command: `mae-eval validate --file <trace.jsonl>`.
  * Add unit tests in `tests/test_schema_validation.py`.
- Document alignment and additions beyond the October 2026 IETF Internet-Draft *"Agent Run Metrics"*.

### Phase 5: Strengthen Scientific Evaluation Protocol
- Define multi-dimensional matching constraints:
  * Equal generated tokens
  * Equal total monetary cost
  * Equal serialized latency
  * Equal independent samples
  * Equal model forward calls
- Implement Pareto frontier calculation in `code/mae_eval/auditor.py` (`compute_pareto_frontier()`).
- Add tests in `tests/test_pareto.py`.

### Phase 6: Checklist Independent Validation Study
- Review `docs/CME_VALIDATION_STUDY.md`.
- Create `experiments/checklist_validation/`:
  * `paper_sample.csv`: Sample of 30 papers across multi-agent debate (8), iterative reflection (8), software agents (7), and single-agent search (7).
  * `rater_worksheet_template.csv`: Standardized scoring sheet for Rater 1 and Rater 2 logging ratings, completion times, and ambiguity scores.
  * `compute_alpha.py`: Script to compute Krippendorff's alpha for nominal ratings.

### Phase 7: Reproducible Example & Software Ecosystem
- Create `code/examples/reproducible_agent_run/`:
  * `raw_execution_trace.jsonl`: Realistic synthetic or measured trace of a 3-agent debate vs. single-agent CoT-SC run.
  * `run_audit.py`: Script demonstrating how an external researcher loads the trace, checks parity conditions, and prints the 6D resource vector table.
  * `expected_output.tex`: Verified LaTeX table generated by the audit script.
- In `code/README.md`: Provide a 10-line quickstart showing how to instrument an agent pipeline in 3 lines of code.

### Phase 8: Rewrite the Adoption Roadmap
- Review `docs/RESOURCE_ACCOUNTING_ADOPTION_ROADMAP.md`.
- Ensure all speculative 6,000-citation projections are removed.
- Anchor the progression to 5 evidence-based stages:
  1. Internal validation (functional toolkit).
  2. Independent checklist validation (30 papers, Krippendorff's $\alpha \ge 0.80$).
  3. Community workshop & voluntary challenge (`docs/WORKSHOP_PROPOSAL_AGENT_EVAL.md`).
  4. Open-source ecosystem integration (adapters for `inspect_ai`, `lm-evaluation-harness`, `OpenHands`).
  5. Institutional discussions with venues (only after demonstrated community uptake).

### Phase 9: Prospective Laboratory Experiment (Phase 3)
- Read `protocol/PROTOCOL.md`.
- Sized for Kaggle Dual-T4 / local GPU on 200 items (100 GSM8K + 100 MATH Level 1–3) using `meta-llama/Llama-3.1-8B-Instruct`.
- Arms: Single Greedy CoT, CoT-SC ($K=3, K=5$), 3-Agent Debate (2 rounds), Budget-Matched Extended CoT.
- Instrument with `mae_eval.ResourceTracker` and evaluate exact paired McNemar statistics and log odds ratios.
- Output to `outputs/phase3_statistical_results.json` and insert findings into manuscript.

### Phase 10: Final Manuscript & Packaging Verification
- Insert the Influential Frameworks Table (`tab:influential_frameworks`) and the positioning statement into `manuscript/section2_related_work.tex`.
- Run `python analysis/assemble_paper.py`.
- Verify `main.pdf` and `tmlr_submission.pdf` compile with **0 errors and 0 undefined references**.
- Run `pytest tests/ -v` to ensure 100% pass rate across all tests.
- Run `python analysis/create_release_bundle.py` to package the updated release zip.

---

## 5. Execution Command for Claude

When starting work in Claude Code, execute this single prompt:

```text
Please read the complete execution specification in docs/CLAUDE_MASTER_EXECUTION_SPEC.md.
Follow the 10-phase roadmap step-by-step.
Begin with Phase 1: audit the environment, verify the installed mae-eval CLI, run pytest across all tests, and confirm that both main.pdf and tmlr_submission.pdf compile cleanly with 0 errors.
Report the exact status of Phase 1 before proceeding to Phase 2.
```
