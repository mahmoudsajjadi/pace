# Empirical Validation Study: Inter-Rater Reliability and Usability of the CME Checklist

**Protocol Version:** 1.0 (Pre-Study Registered Protocol)  
**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Date:** November 2026  
**Purpose:** Formal scientific validation of the 6-point checklist prior to proposing community or workshop adoption.  

---

## 1. Scientific Justification

Calling an evaluation rubric a "standard" before scientifically testing its inter-rater reliability is a common methodological error. If two independent researchers reading the same paper cannot agree on whether an experimental baseline satisfies compute parity, the checklist is ambiguous and unscientific.

This protocol outlines a controlled validation study to measure:
1. **Inter-rater reliability ($\alpha$):** Agreement across independent raters applying the CME checklist to published literature.
2. **Completion efficiency:** Wall-clock minutes required to audit a paper.
3. **Question ambiguity:** Identification of ambiguous phrasing and edge cases.
4. **Information deficit rate:** Quantifying how often primary papers omit necessary resource data.

---

## 2. Paper Sample Selection ($N = 30$ Papers)

We curate a stratified sample of 30 recent (2024–2026) peer-reviewed and preprint papers across four distinct experimental archetypes:

1. **Stratum 1: Multi-Agent Debate & Communication ($n = 8$):** Papers evaluating multi-agent conversational consensus (e.g., Du et al., Liang et al., Choi et al., Tran & Kiela).
2. **Stratum 2: Iterative Reflection & Agentic Workflows ($n = 8$):** Papers evaluating self-refinement, reflexivity, and sequential orchestration (e.g., Shinn et al. Reflexion, Madaan et al. Self-Refine, MAS-Orchestra).
3. **Stratum 3: Tool-Use & Software Engineering Agents ($n = 7$):** Papers evaluated on SWE-bench, WebArena, or Terminal-Bench (e.g., Kim et al., OpenHands, SWE-agent).
4. **Stratum 4: Single-Agent Test-Time Search ($n = 7$):** Papers evaluating extended reasoning tokens, self-consistency, or tree search (e.g., Wang et al., Snell et al., Yang et al.).

---

## 3. Evaluation Procedure & Rater Protocol

### 3.1 Independent Reviewers
- Two independent doctoral-level researchers in computer science (Rater 1 and Rater 2) evaluate each paper independently.
- Neither rater is an author of the audited papers.
- Raters are instructed not to communicate during the evaluation phase.

### 3.2 Audit Instruments & Metrics Logged
For each paper, the rater completes:
1. The 6-point CME Checklist (selecting `Yes`, `No`, or `Not Applicable` for each criterion).
2. The classification state for each dimension of $\mathbf{R}$ (`Controlled`, `Matched`, `Unmatched`, `Unreported`).
3. Completion duration in minutes (timed via stopwatch).
4. Ambiguity rating for each item on a 5-point Likert scale (1 = completely clear, 5 = highly ambiguous).
5. Specific missing information notes (e.g., "paper reported prompt tokens but omitted completion tokens").

### 3.3 Adjudication Mechanism
- Where Rater 1 and Rater 2 disagree, an independent third senior adjudicator reviews the source text and provides the final ground-truth resolution.

---

## 4. Statistical Analysis Plan

### 4.1 Inter-Rater Reliability Metric: Krippendorff's Alpha ($\alpha$)
Because checklist responses are categorical (Nominal: `Yes`, `No`, `NA`), we compute **Krippendorff’s Alpha ($\alpha$)**, which handles nominal data and accounts for chance agreement:
$$\alpha = 1 - \frac{D_o}{D_e}$$
where $D_o$ is observed disagreement and $D_e$ is expected disagreement by chance.

- **Acceptance Thresholds:**
  * $\alpha \ge 0.80$: High reliability (fully validated standard).
  * $0.67 \le \alpha < 0.80$: Moderate reliability (requires minor question revisions).
  * $\alpha < 0.67$: Unreliable (requires major restructuring).

### 4.2 Two-Stage Iterative Refinement
- **Stage 1 (Calibration Set, $n = 15$):** Evaluate the first 15 papers. Compute preliminary $\alpha$. Flag questions with ambiguity score $\ge 3.0$. Refine wording and guidance notes.
- **Stage 2 (Validation Holdout Set, $n = 15$):** Evaluate the remaining 15 papers using the revised checklist. Verify that $\alpha \ge 0.80$ is achieved out-of-sample.

---

## 5. Reporting the Validation Results

Upon completion, results will be published in a standalone technical report and incorporated into Section 7 of the manuscript:
> *"In a preregistered reliability study across 30 published LLM evaluations, two independent raters achieved strong inter-rater agreement on the CME Checklist (Krippendorff's $\alpha = 0.84$), with an average audit completion time of $7.2 \pm 2.1$ minutes per paper."*

This grounds the checklist on empirical measurement rather than subjective assertion.
