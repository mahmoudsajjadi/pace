"""Instrument a LangGraph graph: wrap the client the nodes use and label each node's calls. Needs `pip install langgraph openai`.
Written from the public LangGraph API and not run in this repository's test environment (langgraph is not installed there)."""
from typing import TypedDict

import cme
from langgraph.graph import END, START, StateGraph
from openai import OpenAI

client = cme.wrap(OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"), log_path="cme_trace.jsonl")
class State(TypedDict):
    question: str
    notes: list


def agent(name: str, rnd: int):
    def node(state: State) -> dict:
        with cme.track(agent=name, round=rnd):                       # labels apply to the calls inside this node only
            r = client.chat.completions.create(model="llama3.1:8b", messages=[{"role": "user", "content": state["question"] + "\nNotes: " + str(state["notes"])}])
        return {"notes": state["notes"] + [r.choices[0].message.content]}
    return node


g = StateGraph(State)
g.add_node("a1", agent("a1", 1)); g.add_node("a2", agent("a2", 2))
g.add_edge(START, "a1"); g.add_edge("a1", "a2"); g.add_edge("a2", END)
with cme.track(item_id="item_001", system="mas"):
    out = g.compile().invoke({"question": "What is 17 * 24?", "notes": []})
