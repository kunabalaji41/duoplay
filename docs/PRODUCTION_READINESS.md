# Duopoly Production Readiness Scorecard

Each area scored 1–10. Two scores are given: **As-found** (the inherited state that produced the incidents) and **After fixes** (this review's patches). Scores are deliberately conservative: passing unit tests is not the same as production-proven.

| Area | As-found | After fixes | Evidence | First / Next Improvement |
| --- | ---: | ---: | --- | --- |
| **Security** | 1 | 5 | As-found: public DB open to `0.0.0.0/0`, `alg:none` JWTs accepted, cross-tenant leak, plaintext Stripe key, secrets in logs, allow-all netpol. Fixed: tenant predicates, `alg:none` rejected, private DB, secret refs, default-deny netpol | Cryptographic JWT signature verification (JWKS); central tenant-isolation middleware; secret rotation + scanning in CI |
| **Reliability** | 2 | 6 | As-found: 100×4 retries, breaker off, infinite sub-agent loop, queue-name mismatch, retries with no backoff. Fixed: bounded retries + breaker + backoff, spawn ceiling, queue fix | Distributed/shared circuit-breaker state; idempotency keys to stop duplicate agent actions; integration tests on retry + isolation paths |
| **Scalability** | 3 | 5 | As-found: 80 worker replicas with 50m request / 16-core limit (dishonest bin-packing), no autoscaling signal, per-pod breaker. Fixed: right-sized requests/limits | HPA/KEDA driven by queue depth; backpressure + per-tenant concurrency limits; load test to 500k+ workflows/day |
| **Cost** | 1 | 5 | As-found: billing ignored completion tokens (under-counts vs invoice), retry storm drove $8k→$58k/day egress, no budgets/quotas. Fixed: completion-token billing, capped retries | Per-tenant cost budgets + hard quotas; daily reconciliation vs provider invoices; cost-per-tenant dashboard with alerts |
| **Observability** | 2 | 3 | As-found: pages only on `up==0`/30s-latency; no panels for retries, queue depth, cost-per-tenant, cross-tenant anomalies, or connection saturation; audit unusable. Fixed: audit retains tenant_id/order; logging reduced | Impact-based SLOs (queue age, authorization correctness, invoice reconciliation); the five missing dashboard panels; anomaly alerting |

## Overall

**As-found: ~2/10 — not production-ready.** The platform was one copied workflow ID away from a regulated-data breach, and its defaults amplified rather than contained provider failures, all while dashboards showed green.

**After fixes: ~5/10 — safe to operate under supervision, not yet mature.** The acute incidents are contained and regression-gated by CI. The gap to a strong score is now mostly *observability* (still the lowest, because impact-based signals and the missing panels are not built yet) and the structural items deferred to the roadmap: central tenant isolation, full JWT verification, autoscaling, and cost governance.

### Why observability scores lowest after fixes

Every incident in this case study happened *while monitoring reported healthy*. Until the platform measures user impact — queue age, retry rate, cost-per-tenant, cross-tenant access anomalies, and reconciliation drift — the organization is still flying on instruments that lie. That is the single highest-leverage investment for the next 90 days, which the roadmap front-loads.
