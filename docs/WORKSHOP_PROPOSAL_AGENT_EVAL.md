# Workshop Proposal: AgentEval — Rigorous Evaluation of Multi-Agent Systems, Test-Time Compute, and Autonomous Workflows

**Proposed Venue:** NeurIPS 2027 / ICLR 2028 Workshop Track  
**Workshop Title:** AgentEval: Rigorous Evaluation of Multi-Agent Systems, Test-Time Compute, and Autonomous Workflows  
**Acronym:** AgentEval 2027  
**Proposers & Organizing Committee:**  
- **Seyed Mahmoud Sajjadi Mohammadabadi** (University of Nevada, Reno) [Lead Organizer & CME Track Chair]
- **Target Co-Organizers:** Collaborators from top evaluation initiatives (Stanford CRFM / HELM, EleutherAI, Hugging Face Evaluation Coalition, Contextual AI).

---

## 1. Abstract & Rationale

Large Language Model research is undergoing an architectural shift from static, single-prompt generation toward **agentic workflows**—systems characterized by multi-agent debate, communicative graphs, iterative code generation, and test-time compute search. 

However, the field currently suffers from an acute evaluation crisis:
1. **The Unmatched Compute Confound:** Most multi-agent systems are evaluated against weak greedy baselines, crediting multi-agent communication for accuracy gains that arise strictly from allocating $5\times$ to $50\times$ more inference tokens.
2. **Evaluation Metric Instability:** Benchmarks are contaminated, sample sizes are under-powered, and paired instance variance is rarely reported.
3. **Absence of Shared Standards:** Unlike classical machine learning or foundation model pretraining, there are no universally agreed-upon resource-accounting standards for test-time compute.

**AgentEval** convenes researchers from multi-agent systems, natural language processing, reinforcement learning, and AI meta-science to establish unified evaluation standards. It features the **Compute-Matched Evaluation (CME) Challenge**, piloting standardized resource accounting across conference submissions.

---

## 2. Key Workshop Themes

1. **Inference-Time Scaling vs. Coordination:** When do communicating multi-agent topologies outperform single-agent test-time search (e.g., self-consistency, tree-of-thought, Monte Carlo search)?
2. **Resource-Accounting Protocols:** Measuring the 6D resource vector $\mathbf{R}$ (thinking tokens, total tokens, monetary cost, latency, samples, tool invocations).
3. **Structural Task Taxonomy:** Disentangling tasks that benefit from modular specialization (parallel tool sandboxes, partitioned context windows) from tasks where debate induces context dilution and hallucination cascades.
4. **Reliable Benchmarking for Autonomous Coding & Web Agents:** Preventing metric artifacts and evaluating long-horizon agents (SWE-bench, WebArena, OSWorld).
5. **Conference Policy & Peer Review Standards:** Institutionalizing the CME Reviewer Checklist across top ML venues.

---

## 3. Workshop Format & Program

- **Opening Keynote 1:** "Scaling Inference Compute: What the Scaling Laws Tell Us" (Focus on test-time compute vs. pretraining).
- **Contributed Oral Presentations (Morning):** Top 4 accepted papers on compute-matched agent architectures.
- **Keynote 2:** "The Mechanics of Coordination Failures in Language Models" (Context dilution, echoed bias, and verification).
- **The CME Reproducibility Challenge & Panel Discussion:**
  - *Panel Topic:* "Are Multiple Agents an Illusion? Settling the Baseline Confound in Agentic LLMs."
  - Panelists representing both multi-agent proponents and test-time scaling theorists.
- **Poster Session & Networking:** Featuring all accepted papers with mandatory CME Compliance Badges.
- **Closing Town Hall:** Drafting the "Community Statement on Multi-Agent Evaluation Standards."

---

## 4. The CME Pilot Track (Call for Papers)

Submissions to AgentEval will be invited in two tracks:
- **Track 1: Original Research & Architectures (4–8 pages):** Novel multi-agent protocols, test-time search methods, and empirical benchmark audits.
- **Track 2: Reproducibility & Benchmark Audits (2–4 pages):** Re-evaluations of published multi-agent papers under strictly matched compute budgets.

**Mandatory Submission Requirement:**  
Every submission to AgentEval must complete the **6-point CME Reviewer Checklist**. Submissions that demonstrate compute parity with single-agent baselines or transparently audit their resource vector $\mathbf{R}$ will be eligible for the **Best Compute-Matched Evaluation Award**.

---

## 5. Potential Keynotes & Advisory Board

*(Invitations to be extended upon proposal approval)*
- **Percy Liang** (Stanford University, CRFM / HELM) — Leader in foundation model evaluation.
- **Sanmi Koyejo** (Stanford University) — Co-author of *Are Emergent Abilities a Mirage?* and leader in ML evaluation.
- **Douwe Kiela** (Contextual AI / Stanford) — Pioneer in dynamic benchmarking and author of *Thinking Tokens Parity*.
- **Joelle Pineau** (McGill University / FAIR) — Creator of the NeurIPS Reproducibility Checklist.
- **Jesse Dodge** (Allen Institute for AI) — Architect of NLP compute and environmental reporting standards.

---

## 6. Expected Outcomes & Institutional Impact

1. **Pilot Data for Conference Leadership:** Results from the CME pilot track will be compiled into a white paper and presented directly to the NeurIPS 2028 and ICLR 2028 Program Chairs as empirical evidence of the checklist's viability.
2. **Open-Source Standard (`mae-eval`):** The workshop will establish `mae-eval` as the community-standard reference library for agent benchmarking.
3. **Proceedings & Community Canon:** Workshop proceedings will be archived on OpenReview, establishing a citable body of work that compounds citations across subsequent conference cycles.
