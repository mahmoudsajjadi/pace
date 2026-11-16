"""pace_lab: client layer, data loaders and graders for the controlled experiments (Phase 4.1-4.4).

Submodules (import them explicitly; nothing here touches the network or reads a key at import time):
    pace_lab.clients           logged, cached, resumable LLM calls for Ollama, Groq and Gemini
    pace_lab.concurrency_test  OLLAMA_NUM_PARALLEL throughput/VRAM script (run by the author, needs the GPU)
    pace_lab.data              benchmark loaders with an id + SHA-256 manifest under data/pace_lab/
    pace_lab.graders           multiple-choice, math and hidden-profile answer extraction and grading
"""
__version__ = "0.1.0"
