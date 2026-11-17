# The CME Conference Endorsement Playbook: Roadmap to 6,000+ Citations

**Project:** Compute-Matched Evaluation (CME) Standard & Protocol  
**Author:** Seyed Mahmoud Sajjadi Mohammadabadi  
**Affiliation:** University of Nevada, Reno (`mahmoud.sajjadi@unr.edu`)  
**Target Conferences:** NeurIPS, ICLR, ICML, ACL, EMNLP, TMLR  
**Target Milestone:** Official Adoption by Conference Submission Portals (OpenReview / HotCRP / CMT)  
**Long-Term Horizon:** 2026–2035 Cumulative Citations $\ge 6{,}000$  

---

## Executive Summary: How Reviewer Checklists Reach Canon Status

In modern machine learning, **only papers that alter the institutional evaluation infrastructure surpass 5,000+ citations without proposing a new foundation model**. 

Two historical precedents define this playbook:
1. **The NeurIPS Reproducibility Checklist (Joelle Pineau et al., 2019–2020):**  
   Transitioned from an academic critique into an institutional requirement on OpenReview. Over 15,000 submissions per year are required to fill out the checklist, forcing thousands of papers annually to cite the underlying methodology.
2. **Show Your Work / Energy & Compute Reporting (Jesse Dodge, Roy Schwartz, Noah Smith et al., 2019–2020):**  
   Partnered with ACL/EMNLP leadership to mandate compute reporting in natural language processing, making carbon and token disclosures standard practice across NLP proceedings.

To achieve official endorsement for the **CME Reviewer Checklist**, we must satisfy three criteria required by Program Chairs:
- **Zero Friction for Authors:** The checklist must take $< 10$ minutes to fill out and provide automated CLI tools.
- **Zero Friction for Reviewers:** It must provide binary radio buttons and an objective decision rubric that resolves review ambiguities in $< 90$ seconds.
- **Non-Punitive Design:** It must be an **accounting disclosure standard**, not a ban on exploratory multi-agent systems. Papers with unmatched compute are not desk-rejected; they simply disclose the confound.

---

## 5-Phase Master Execution Timeline (2026–2028)

```
2026 Q4 (Nov-Dec): Freeze Manuscript + Phase 3 Experiment + Open-Source Tooling (mae-eval)
      │
2027 Q1 (Jan-Mar): TMLR Acceptance + arXiv Release + Zenodo DOI + Pre-Print Outreach
      │
2027 Q2 (Apr-Jun): Launch CME-O Living Observatory + Form "AgentEval" Community Coalition
      │
2027 Q3 (Jul-Sep): Host/Submit NeurIPS/ICLR Workshop Proposal + Pilot Checklist in Challenge
      │
2027 Q4 - 2028 Q1: Formal Petition to NeurIPS/ICLR Program Chairs for Official CFP Integration
      │
2028 - 2035:       Mandatory OpenReview Integration -> 600-800 Citations/Year Compounding
```

---

## Phase 1: Foundation & Turnkey Packaging (November – December 2026)

Before approaching conference steering committees, the standard must be mathematically rigorous, validated with primary experiments, and supported by open-source software.

### Milestone 1.1: Finalize Phase 3 Laboratory Experiment
- **Objective:** Prevent any "desk-rejection" under TMLR's survey rules by pairing the 252-contrast meta-audit with primary experimental validation.
- **Protocol:** Run `protocol/PROTOCOL.md` (Llama-3.1-8B-Instruct on 200 GSM8K/MATH items across Greedy, CoT-SC (3, 5), 3-Agent Debate, and Budget-Matched CoT).
- **Deliverable:** Add Section 6 ("Prospective Laboratory Verification") to `main.tex` and `tmlr_submission.tex` with paired McNemar statistics.

### Milestone 1.2: Package `mae-eval` for One-Line Installation
- **Objective:** Give researchers a zero-barrier command-line utility.
- **Execution:** Publish `mae-eval` on PyPI (`pip install mae-eval`).
- **Feature Additions:**
  - `mae-eval audit --log trace.jsonl --baseline cot-sc-5`
  - `mae-eval checklist --export-latex` (generates `cme_checklist_table.tex` ready to paste into submission appendices).
  - Automated detection of whether thinking tokens, total tokens, or cost are matched within 5% tolerance.

### Milestone 1.3: Author-Facing Compliance Assets
- Create `docs/CME_AUTHOR_COMPLIANCE_GUIDE.md`: A 2-page guide explaining how an author can audit their multi-agent paper in 15 minutes before submitting.
- Create `docs/CME_OPENREVIEW_FORM_SPEC.json`: Machine-readable JSON ready for OpenReview form builders.

---

## Phase 2: Publication & Strategic Pre-Print Dissemination (January – March 2027)

How the paper is released determines whether it is received as a hostile takedown or an indispensable methodological breakthrough.

### Milestone 2.1: TMLR Publication & arXiv Announcement
- Once accepted at TMLR, release camera-ready version on arXiv (`cs.AI`, `cs.LG`, `cs.CL`) and mint permanent Zenodo DOI.
- Structure the announcement around **constructive solutions**, not just critique:
  - Lead with: *"When do multiple LLM agents actually beat one? A synthesis of 252 contrasts shows that gains disappear when compute and samples are matched, EXCEPT when task structure has genuine decomposability or external verifiers. Here is the decision heuristic and the CME evaluation checklist."*

### Milestone 2.2: Courteous Advance Outreach to Primary Authors
- Before public social circulation, email brief, respectful notes to key authors of the five audited studies:
  - **Douwe Kiela & Son Tran** (Contextual AI / Tran & Kiela 2026)
  - **Pranava Swaroop Jwalapuram et al.** (Jwalapuram et al. 2026)
  - **Jihye Choi et al.** (Choi et al. / NeurIPS 2025 Spotlight)
  - **Google-MIT Authors** (Kim et al. 2026 / Nature Machine Intelligence)
  - **Wunderlich et al.** (Göttingen / Mixture of Agents)
- **Message Framing:**
  > *"Dear Dr. [Name], we conducted a systematic synthesis of compute-matched evaluations in multi-agent LLMs, anchoring our analysis directly on the transparent data from your recent paper [Title]. Your reporting was instrumental in clarifying test-time compute scaling. We have cited your methodology as an exemplar of rigorous extraction and wanted to share the preprint with you."*
- **Outcome:** Turning audited authors into citing allies and vocal champions who recommend the CME standard in their peer reviews.

---

## Phase 3: The "AgentEval" Community Coalition & Living Observatory (April – September 2027)

Conferences adopt checklists when a **coalition of prominent researchers requests it**, rather than a single individual.

### Milestone 3.1: Launch the CME-O Living Observatory
- Host a public dashboard on GitHub Pages and Hugging Face Spaces: `https://agent-eval.org` or `https://huggingface.co/spaces/cme-observatory`.
- Live auditing of new multi-agent frameworks:
  - Whenever a new lab drops a system (e.g., AutoGen 0.4, LangGraph Multi-Agent, CrewAI, Swarm, Devin/SWE-agent updates), run the CME audit on their reported benchmarks.
  - Display the interactive 2D Pareto Frontiers ($\Delta\text{Accuracy}$ vs $\Delta\text{Tokens}$ / $\Delta\text{Cost}$).
- **Citation Loop:** Every blog post, tweet, and paper analyzing agent frameworks will link to the Observatory for third-party validation.

### Milestone 3.2: Assemble the Steering Committee & Open Letter
- Form the **Compute-Matched Agent Evaluation (CME) Working Group**.
- Invite 5–8 respected researchers in LLM evaluation, reproducibility, and agent benchmarking to co-author an open letter:
  - Target Co-Signers: Leading reproducibility chairs (e.g., Joelle Pineau, Jesse Dodge, Sanmi Koyejo, Colin Raffel, Percy Liang / HELM team).
  - Document: *"Open Letter on Evaluation Rigor for Autonomous and Multi-Agent LLMs"* published on arXiv and OpenReview.

### Milestone 3.3: Submit a Dedicated Workshop Proposal
- Submit workshop proposal for **NeurIPS 2027** or **ICLR 2028**:
  - *Title:* "AgentEval: Workshop on Rigorous Evaluation of Multi-Agent Systems and Test-Time Compute".
  - *Format:* Include a **CME Reproducibility Track** where submissions must include a filled CME checklist.
  - *Precedent:* NeurIPS Reproducibility Challenge 2019 piloted the checklist before conference-wide adoption in 2020.

---

## Phase 4: Institutional Endorsement by Major Conferences (Q4 2027 – Q1 2028)

This is the decisive institutional pivot that scales citations from hundreds to thousands.

### Step-by-Step Conference Submission Pitch Plan:

1. **Targeting NeurIPS / ICLR Program Chairs:**
   - Every year in January/February, NeurIPS and ICLR appoint new General Chairs, Program Chairs, and **Reproducibility / Ethics Chairs**.
   - Send the formal proposal: [`docs/CME_CHECKLIST_OFFICIAL_PROPOSAL.md`](file:///c:/Users/17756/OneDrive%20-%20University%20of%20Nevada,%20Reno/Projects/Automation/01_Research/Manuscripts/01_pure_ml_reasoning_and_test_time_compute/docs/CME_CHECKLIST_OFFICIAL_PROPOSAL.md).
2. **Present the Turnkey OpenReview Integration:**
   - Hand the Program Chairs the ready-made OpenReview JSON specification (`docs/CME_OPENREVIEW_FORM_SPEC.json`).
   - Highlight that the CME Checklist directly addresses the #1 complaint of multi-agent reviewers: *"Is this actual coordination or just 5x the tokens?"*
3. **The Two-Stage Rollout Strategy (Overcoming Resistance):**
   - **Year 1 (Pilot):** The CME Checklist is introduced as **"Strongly Recommended"** for all submissions in the Agent, LLM Reasoning, and Systems tracks. Authors receive a CME Compliance Badge in their OpenReview forum.
   - **Year 2 (Full Mandate):** The CME Checklist becomes **mandatory** for all submissions in the Agent / Reasoning tracks, matching the General NeurIPS Paper Checklist.

---

## Phase 5: Sustained Growth & Citation Compounding (2028–2035)

Once the checklist is embedded in the submission portal, citation compounding shifts into an automatic institutional cycle:

```
[Conference CFP Mandates CME Checklist]
                  │
                  ▼
[1,000+ Multi-Agent Submissions / Year Must Complete Checklist]
                  │
                  ▼
[Authors Must Cite CME Protocol in Experimental Setup (Mohammadabadi, 2026)]
                  │
                  ▼
[Reviewers Cite CME Rubric in Reject/Accept Decisions]
                  │
                  ▼
[Annual Growth: 600 - 800 Citations / Year]
                  │
                  ▼
[Cumulative Total by 2035: 6,000+ Citations]
```

### Citation Milestones by Year under Full Endorsement:

- **2026:** 10 citations (Preprint release, laboratory protocol)
- **2027:** 120 citations (TMLR publication, `mae-eval` PyPI release, Workshop pilot)
- **2028:** 520 citations (First NeurIPS/ICLR cycle with recommended CME track)
- **2029:** 1,220 citations (Full mandate across NeurIPS/ICLR/ICML agent tracks)
- **2030:** 2,050 citations (Textbooks and survey chapters adopt 6D vector $\mathbf{R}$)
- **2031:** 2,900 citations (Expansion to embodied robotics & multimodal agents)
- **2032:** 3,800 citations (Standard baseline in all enterprise agent benchmarks)
- **2033:** 4,650 citations (Long-term reference for inference scaling laws)
- **2034:** 5,450 citations (Historical canon status)
- **2035:** **6,200+ citations**

---

## Immediate Action Items

1. [x] Complete text overhaul across manuscript modules conforming to all style rules.
2. [x] Recompile preprint (`main.pdf`) and blind submission (`tmlr_submission.pdf`) with 0 errors / 0 undefined references.
3. [x] Run full test suite (`pytest tests/ -q`) $\to$ 182 passed (100%).
4. [x] Draft and freeze Phase 3 Laboratory Protocol (`protocol/PROTOCOL.md`).
5. [ ] Formulate Formal Conference Proposal Document (`docs/CME_CHECKLIST_OFFICIAL_PROPOSAL.md`).
6. [ ] Generate OpenReview Machine-Readable Schema (`docs/CME_OPENREVIEW_FORM_SPEC.json`).
7. [ ] Write Author Compliance Guide (`docs/CME_AUTHOR_COMPLIANCE_GUIDE.md`).
8. [ ] Draft Workshop Proposal (`docs/WORKSHOP_PROPOSAL_AGENT_EVAL.md`).
9. [ ] Implement CLI checklist generator in `code/mae_eval/cli.py`.
