"""Instrument CrewAI, which sends its model calls through litellm: wrap litellm's `completion` and label the kickoff. Needs `pip install crewai litellm`.
Written from the public CrewAI and litellm APIs and not run in this repository's test environment (crewai is not installed there). CrewAI may run
tasks in worker threads; if calls appear without labels, wrap the kickoff inside each worker or check that your version propagates context variables."""
import pace
import litellm
from crewai import Agent, Crew, Task

litellm.completion = pace.wrap(litellm, log_path="pace_trace.jsonl").completion    # CrewAI calls litellm.completion at call time

llm = "ollama/llama3.1:8b"
a = Agent(role="solver", goal="Answer arithmetic questions", backstory="A careful solver.", llm=llm)
b = Agent(role="checker", goal="Check an answer", backstory="A careful checker.", llm=llm)
tasks = [Task(description="Compute 17 * 24.", expected_output="A number", agent=a), Task(description="Check the previous answer.", expected_output="A number", agent=b)]
with pace.track(item_id="item_001", system="mas"):
    result = Crew(agents=[a, b], tasks=tasks).kickoff()
pace.log_result("pace_trace.jsonl", "item_001", correct="408" in str(result), system="mas")
