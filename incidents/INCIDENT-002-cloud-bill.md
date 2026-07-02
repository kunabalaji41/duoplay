# Incident 002: Cloud Bill Spike

Time: Tuesday 02:00

Symptoms:

- Daily cloud and provider bill increased from 8,000 USD to 58,000 USD.
- LLM gateway egress increased sharply.
- Billing dashboard under-reported customer usage.

Initial observation:

- Several tenants had failed LLM requests retried many times.
- Completion tokens appear lower than provider invoice numbers.
- Gateway logs include request headers.

Candidate tasks:

- Identify billing under-counting and retry amplification.
- Estimate blast radius.
- Recommend guardrails for retry budgets, cost budgets, and tenant quotas.

