# Incident 001: LLM Latency and Queue Backlog

Time: Monday 09:00

Symptoms:

- OpenAI request latency reached 25 seconds.
- Workflow queues backed up.
- Agent workers saturated CPU.
- Customers reported delayed approvals and duplicate agent actions.

Initial observation:

- Gateway logs contain repeated calls to fallback providers.
- Prometheus dashboard still shows gateway availability as green.
- Worker queue depth was not visible on the main dashboard.

Candidate tasks:

- Find the likely retry and fallback failure mode.
- Explain why queue saturation followed provider latency.
- Propose immediate mitigation and long-term fix.

