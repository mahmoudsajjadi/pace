# MASTER BRIEF

Saved verbatim from the author's message of 2026-11-13. Re-read at the start of every session.

Project root:
C:\Users\17756\OneDrive - University of Nevada, Reno\Projects\Automation\01_Research\Manuscripts\01_pure_ml_reasoning_and_test_time_compute

Paper: "More Agents, More Samples, or More Thinking? ..." Two builds:
- manuscript/tmlr_submission.pdf (anonymized, for TMLR)
- manuscript/main.pdf (named, for arXiv)
Both must have identical scientific content and an identical AI-use statement.

Hardware and services: RTX 4070 12 GB with Ollama (llama3.1:8b, qwen3:14b, gemma4:12b,
deepseek-r1:8b/14b, qwen2.5-coder:7b/14b, olmo-3:7b); Groq free tier (gpt-oss-20b, gpt-oss-120b,
qwen3.8-27b; needs a User-Agent header); Gemini free tier (small subsets only).

RULES (non-negotiable)
1. Never invent data, numbers, citations, author lists, quotes or verification. If something cannot
   be checked, say so and leave it blank.
2. Never present synthetic, simulated, pilot or placeholder data as real. Every synthetic file has
   "synthetic": true and is called synthetic in the paper.
3. A task is done only with evidence in STATUS.md: the command, its trimmed output, file paths, and
   for paper changes the matching lines from pdftotext of the rebuilt PDF.
4. Stop at every [ME] step and wait for my answer. Never guess it.
5. Never push, publish, upload or register anything (GitHub, PyPI, Hugging Face, Zenodo, OSF,
   arXiv) without my explicit approval in chat.
6. AI-use disclosure: never weaken it. The page-1 footnote stays. It states that AI tools extracted
   values, screened studies, wrote the analysis code, the package and tests, ran the programmatic and
   stratified checks, and drafted and edited text, plus exactly what I checked by hand (ask me).
7. Secrets: keys only from environment variables or a gitignored .env. Never print, log, commit or
   pass keys on the command line.
8. Spending: local models and free tiers by default. Ask before any paid call; never exceed the
   budget I approve.
9. Windows/PowerShell: use $LASTEXITCODE (not $?), Get-Content -Tail, Select-String. Never search
   C:\ or C:\Program Files recursively. Long runs go in the background with log files and must
   resume from cache.
10. Keep STATUS.md current: date, phase, task, status (todo/doing/done/blocked), evidence, and open
    questions for me.
11. Commit locally after each task. No force-push and no history rewrite without approval.
12. Run pytest after every code change. A phase is done only when its "Done when" list is met.
