# LLM Gateway

Routes chat requests across OpenAI, Anthropic, Gemini, and Azure OpenAI.

Known production concerns:

- Provider latency should not create retry storms.
- Costs must include all billable token classes.
- Logs must never expose API keys.
- Provider failures should trip circuit breakers.

Candidate starting point: `app.py`.

