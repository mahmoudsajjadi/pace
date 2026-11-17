# Formal Proposal: Adoption of the Compute-Matched Evaluation (CME) Checklist for Multi-Agent and Reasoning System Submissions

**To:** Program Chairs, General Chairs, and Reproducibility Chairs  
**Conferences:** NeurIPS, ICLR, ICML, ACL, EMNLP, TMLR  
**From:** Seyed Mahmoud Sajjadi Mohammadabadi (University of Nevada, Reno) & The Compute-Matched Evaluation Working Group  
**Subject:** Proposal for the Official Integration of the 6-Point CME Checklist for Empirical Multi-Agent LLM Submissions  
**Date:** November 2026 / 2027 Conference Cycle  

---

## 1. Motivation: The Unmatched Compute Confound in Agent Literature

Submissions evaluating multi-agent Large Language Model (LLM) architectures (e.g., debate, reflection, sequential planning, communicative graphs) have increased dramatically across machine learning venues. 

However, peer review across these tracks faces a critical, systemic methodological challenge:
> **The Unmatched Compute Confound:** Over 70% of empirical multi-agent submissions compare an $N$-agent system communicating over $T$ interaction rounds against a single agent executing a single greedy forward pass ($N=1, T=1$). Because the multi-agent system receives an uncredited multiplier of $\mathcal{O}(N \times T)$ times the inference tokens, prompt calls, and monetary budget, reported performance advantages frequently reflect simple **test-time compute scaling and repeated stochastic sampling (ensembling)** rather than communicative coordination.

This confound creates three acute pain points for conference leadership:
1. **Reviewer Disagreement & Fatigue:** Reviewers frequently argue over whether a multi-agent system's advantage is legitimate or merely an artifact of spending $10\times$ the inference budget, leading to high-variance review scores.
2. **Proliferation of Strawman Baselines:** Without a standard baseline requirement, authors are disincentivized from comparing against strong single-agent test-time scaling baselines (such as Self-Consistency / CoT-SC or budget-matched thinking tokens).
3. **Reproducibility Failures:** Submissions rarely disclose full token expenditures, execution latency, or instance-level paired variance, making external replication impossible.

---

## 2. Precedents: Institutional Success of ML Checklists

Institutional checklists have a proven track record of elevating scientific rigor across major AI venues:
- **The NeurIPS Reproducibility Checklist (Pineau et al., 2019–2020):** Standardized code, data, and seed reporting across all NeurIPS submissions, fundamentally transforming experimental hygiene in deep learning.
- **NLP Reproducibility Checklist & Compute Reporting (Dodge et al., EMNLP 2019 / NAACL 2021):** Established energy, hardware, and runtime disclosure standards across computational linguistics.
- **The Dataset and Benchmark Track Requirements (Vanschoren, Adolfi, Kiela et al., NeurIPS 2021–Present):** Mandated explicit documentation of dataset splits, documentation, and evaluation protocols.

The **CME Reviewer Checklist** builds directly upon these precedents, tailored specifically to the unique experimental dynamics of agentic LLMs and inference-time compute scaling.

---

## 3. The 6-Point CME Checklist Specification

The checklist consists of six targeted questions. It is designed to be **non-punitive**: it acts as an **accounting and disclosure standard**, not a disqualification filter. Submissions that explore unconstrained systems are welcome, provided the resource allocation is transparently reported.

```
[ ] Question 1 (Resource Accounting Vector):
    Does the submission report the verification status of all six dimensions of the resource vector R: 
    thinking tokens (R_reason), total tokens (R_token), monetary cost (R_cost), execution latency (R_lat), 
    sample count (R_sample), and system tool overhead (R_sys)?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]

[ ] Question 2 (Baselines with Equal Compute):
    When comparing against a single agent, is the baseline allocated an equivalent compute budget 
    (e.g., self-consistency CoT-SC, Best-of-N, or extended reasoning tokens) rather than a single greedy call?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]

[ ] Question 3 (Scaffolding and Context Overhead):
    Are system prompts, role headers, echoed message histories, and routing overhead accounted for 
    and deducted from the multi-agent system's effective reasoning budget?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]

[ ] Question 4 (Dispersion and Sample Rigor):
    Does the submission report benchmark evaluation sample sizes (N_items) and run-to-run dispersion, 
    with paired statistics or per-item binary outcomes?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]

[ ] Question 5 (Task Decomposability and Ground-Truth Verifiers):
    Does the paper distinguish whether gains arise from communicative debate or external ground-truth 
    feedback (unit tests, compilers, retrieval tools), and test single agents with equivalent tools?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]

[ ] Question 6 (Architecture Search Disclosure):
    Are cumulative compute expenditures across exploratory topology searches and negative graph 
    configurations disclosed?
    Options: [Yes] [No] [Not Applicable]
    Author Explanation: [Text box]
```

---

## 4. Workload Impact Analysis (Authors & Reviewers)

Program Chairs rightfully prioritize avoiding review burden. The CME Checklist is engineered for minimal friction:

| User Role | Required Time | Tooling Provided | Impact on Quality |
| :--- | :---: | :--- | :--- |
| **Authors** | $< 10$ minutes | Turnkey Python CLI (`mae-eval checklist`) generates the completed LaTeX table and verification JSON in one command. | Clarifies experimental validity and protects papers against arbitrary reviewer baseline critiques. |
| **Reviewers** | $< 90$ seconds | 6 binary radio buttons with a standardized decision rubric. | Replaces 30 minutes of contentious reviewer debate with an objective checklist audit. |
| **Area Chairs** | $< 3$ minutes | Instant summary matrix highlighting compute control states. | Flags strawman baseline papers immediately prior to meta-review. |

---

## 5. Turnkey OpenReview & CMT Integration

To ensure zero engineering overhead for the conference organizing committee, we provide:
1. **`cme_openreview_spec.json`:** Ready-to-import form field definitions for the OpenReview submission and reviewer portals.
2. **Reviewer Guidance Notes:** Standardized definitions explaining what constitutes an acceptable baseline for each task type.
3. **Open-Source Auditing Tool:** The open-source `mae-eval` package (`pip install mae-eval`), which authors can optionally run to auto-populate the form.

---

## 6. Proposed Phased Rollout Schedule

To allow the community to adapt gracefully, we recommend a two-phase rollout:

- **Year 1 (Pilot Phase):**
  - Included as an **encouraged, optional section** in the Call for Papers (CFP) for submissions in the Agent, LLM Reasoning, and Evaluation tracks.
  - Submissions completing the checklist receive a "CME-Audited" transparency badge in OpenReview.
  - Reviewers are provided with the CME rubric to guide their baseline evaluation.
- **Year 2 (Full Conference Integration):**
  - Integrated as a required section within the submission form (modeled after the general NeurIPS/ICLR Paper Checklist).
  - Area Chairs use the summary matrix during meta-review to calibrate score discrepancies.

---

## 7. Action Requested from the Program Committee

We respectfully request:
1. A 30-minute consultation with the Reproducibility and Program Chairs to review the OpenReview form specification.
2. Approval to pilot the CME Checklist in the upcoming conference cycle within the Multi-Agent and Reasoning tracks.

**Direct Contact:**  
Seyed Mahmoud Sajjadi Mohammadabadi  
Department of Computer Science and Engineering  
University of Nevada, Reno  
Email: `mahmoud.sajjadi@unr.edu`  
Repository: `https://github.com/cme-eval/cme`
