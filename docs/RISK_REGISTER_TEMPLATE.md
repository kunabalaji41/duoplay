# Risk Register Template

| Risk | Impact | Likelihood | Priority | Evidence | Proposed Fix |
| --- | --- | --- | --- | --- | --- |
| Cross-tenant workflow access | Critical | High | P0 | Tenant lookup path | Add tenant-scoped access checks and tests |
| Retry storm during provider latency | High | High | P0 | Gateway retry behavior | Retry budget, backoff, circuit breaker |
| Billing under-counting | High | Medium | P1 | Usage calculation | Include completion tokens |

