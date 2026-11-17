"""Log every call of an OpenAI-compatible client with cme.wrap, then audit the log. Needs `pip install openai` and a server (here Ollama)."""
import cme
from openai import OpenAI

LOG = "cme_trace.jsonl"
client = cme.wrap(OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"), log_path=LOG)   # prices omitted: cost stays null
ask = lambda q: client.chat.completions.create(model="llama3.1:8b", messages=[{"role": "user", "content": q}]).choices[0].message.content

with cme.track(item_id="item_001", system="sas", agent="solver", round=0):        # the single-agent baseline: one call
    answer = ask("What is 17 * 24? Answer with the number only.")
with cme.track(item_id="item_001", system="mas"):                                  # the multi-agent system: three agents, two rounds
    drafts = []
    for rnd in (1, 2):
        for agent in ("a1", "a2", "a3"):
            with cme.track(agent=agent, round=rnd):
                drafts.append(ask("Previous answers: %s\nWhat is 17 * 24? Answer with the number only." % drafts[-3:]))
cme.log_result(LOG, "item_001", correct=drafts[-1].strip() == "408", system="mas")
print("then: python -m cme audit %s --baseline-config sas.json" % LOG)             # sas.json: {"n_samples": 1}
