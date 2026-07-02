# Duopoly Platform — Architecture Review

**Author:** Incoming Head of AgentOps
**Scope:** Production platform review following three customer-impacting incidents
**Scale reviewed:** 250 tenants, ~8,000 active agents, ~500k workflow executions/day, 4 LLM providers, 3 cloud providers

---

## 1. Executive Summary

Duopoly is a multi-tenant AI Agent Operating System. The platform's service decomposition is reasonable, but it is **not production-ready in its current state**. Three live incidents (LLM latency/queue backlog, a 7x cloud bill spike, and cross-tenant workflow visibility) are not independent — they share a small number of root causes that the platform's defaults actively amplify.

The single most important finding is a **cross-tenant data exposure (P0)**: workflow lookups accept a `tenant_id` argument but never use it in the query predicate, so any tenant can read any other tenant's workflow by ID. For an enterprise platform serving banks and pharma, this is a critical security incident requiring containment, notification, and audit reconstruction — yet the audit service was simultaneously dropping the very `tenant_id` field needed to investigate.

The reliability and cost incidents share a root cause too: an unbounded retry budget (100 retries × 4 providers ≈ 400 attempts per request) with the circuit breaker disabled. When OpenAI slowed down, the gateway amplified load instead of shedding it, which backed up workflow queues, saturated workers, and multiplied egress and token spend. Billing then *under-reported* this because it only charged for prompt tokens, hiding the blast radius from the people who could have caught it.

I have fixed the highest-priority issues with small, defensible patches (all 8 previously failing tests now pass) and hardened the most dangerous infrastructure. The remaining work is laid out in the 90-day roadmap. **Do not trust the green dashboards**: availability was reported as healthy throughout all three incidents because the platform measures pod uptime and HTTP 200 rate rather than user impact.

---

## 2. Architecture Overview

### 2.1 Request path (as documented)

1. Tenant dashboard / SDK → request
2. **Tenant Manager** resolves tenant, plan, workflow metadata
3. **Workflow Engine** schedules long-running execution (Temporal-like queues)
4. **Agent Runtime** plans and issues tool calls, may spawn sub-agents
5. **LLM Gateway** routes provider requests with fallback
6. **Vector Service** retrieves memory context
7. **Billing Service** records token/storage/workflow/agent usage
8. **Audit Service** records security-sensitive operations
9. **Deployment Manager** promotes agent versions to Kubernetes
10. **Monitoring** collects operational signals

### 2.2 Trust boundaries

- Public API → LLM Gateway and Tenant Manager
- Tenant dashboard → workflow metadata APIs
- Agent Runtime → tool execution and deployment APIs
- Deployment Manager → Kubernetes cluster credentials
- Billing events → customer invoices
- Audit events → incident response / compliance evidence

### 2.3 Structural assessment

The service boundaries are sensible and map to distinct failure and scaling domains. The critical weakness is **horizontal**: tenant isolation is treated as a per-call convention (a `tenant_id` parameter that each service is trusted to honor) rather than a centrally enforced invariant. The documented technical debt ("tenant context is passed manually instead of enforced centrally") is not a cosmetic issue — it is the direct cause of Incident 003. Any service that forgets to apply the predicate silently leaks data, and there is no shared guardrail to catch it.

---

## 3. Incident Analysis

### 3.1 Incident 003 — Cross-tenant workflow visibility (CRITICAL / P0)

**Evidence:** `services/tenant-manager/db.py`

```sql
SELECT * FROM workflows WHERE workflow_id = ?      -- tenant_id accepted but unused
```

The function signature is `get_workflow_by_id(workflow_id, tenant_id)`, the `tenant_id` is logged, but it never appears in the filter. A tenant who copies or guesses another tenant's workflow ID receives that record. Support could reproduce it because the bug is deterministic, not a race.

This was made worse by two compounding defects:
- **Vector Service** (`search.py`) ranked documents across *all* tenants, the same isolation gap on the memory-retrieval path.
- **Audit Service** (`audit.py`) discarded `tenant_id` on flush, capped its buffer at 3 events (dropping the rest), and flushed in reverse order, making "which tenant accessed this record" unanswerable during exactly the kind of investigation this incident demands.

**Fix applied:** tenant predicate added to the workflow lookup and vector search; audit now retains `tenant_id`, preserves FIFO order, and flushes durably instead of dropping events. Tests `test_workflow_lookup_is_tenant_scoped`, `test_vector_search_is_tenant_scoped_and_closes_connections`, and `test_audit_flush_preserves_tenant_and_order` now pass.

**Containment / blast radius:** see the security runbook and the roadmap. Because audit logs were lossy, blast-radius reconstruction must fall back to gateway/app logs and DB query logs for the exposure window.

### 3.2 Incident 001 — LLM latency and queue backlog (P0)

**Evidence:** `services/llm-gateway/app.py`

```python
MAX_RETRIES = 100
CIRCUIT_BREAKER_ENABLED = False
```

The retry loop iterates `MAX_RETRIES` times across all four providers, so a single failing request could generate up to ~400 provider calls with no backoff and no breaker. When OpenAI latency rose to 25s, the gateway did not shed load — it multiplied it. That is why **queue saturation followed provider latency**: each slow request held a worker longer and spawned retries, workers saturated CPU, the queue depth grew, and customers saw delayed approvals and **duplicate agent actions** (the same workflow retried and partially re-executed).

The `agent-runtime` made this worse: `run()` looped until a 95% confidence target with no spawn ceiling, and `estimate_confidence` returns 0 for any task containing "research" — an infinite sub-agent spawn loop that pins workers indefinitely.

**Fix applied:** `MAX_RETRIES = 3`, circuit breaker enabled with a per-provider failure threshold and exponential backoff between rounds; `MAX_SUBAGENTS = 5` hard ceiling in the runtime. Tests `test_gateway_retry_budget_is_bounded` and `test_agent_runtime_has_spawn_limit` pass. I also fixed a queue-name mismatch in `workflow-engine/worker.py` (`agent-workflow-prod` vs `agent-workflows-prod`) where submitted work was never consumed.

**Why the dashboard stayed green:** the Prometheus rule pages only when `up == 0` for 5m or average latency `> 30s` for 15m. A gateway returning HTTP 200 after retrying is "available," and queue depth has no panel at all. Availability was healthy while users were not.

### 3.3 Incident 002 — Cloud bill spike, $8k → $58k/day (P0/P1)

This is the same retry storm viewed through the cost lens. Two amplifiers:

1. **Retry amplification → egress and token spend.** Up to ~400 attempts per failing request multiplied provider egress; the incident notes confirm "gateway egress increased sharply" and "failed LLM requests retried many times."
2. **Billing under-counting hid it.** `services/billing-service/billing.py` charged `prompt_tokens` only and ignored `completion_tokens` — which are both higher-volume and higher-priced. The invoice therefore drifted *below* the real provider bill ("completion tokens appear lower than provider invoice numbers"), so the cost signal that should have raised an alarm was suppressed.

A third issue, **secret exposure**: gateway logs included request headers and `redact_headers` was a no-op, so `Authorization`/API keys were written to logs.

**Fix applied:** billing now charges prompt + completion tokens (`usage_charge("openai", 1000, 9000) == 0.28`, test passes); the gateway's `estimate_cost` includes completion tokens; `redact_headers` redacts `authorization`/`x-api-key`/`cookie` while preserving `traceparent` (test passes). The bounded retry budget from 3.2 directly caps the cost blast radius going forward.

**Estimated blast radius:** with retries cut from up to ~400 to at most ~12 attempts/request (3 rounds × 4 providers) and the breaker skipping a sick provider, worst-case amplification drops by ~30x. Exact recovery depends on the share of the $58k attributable to retried failures vs. legitimate growth — quantify from gateway attempt counts once the retry/cost panels exist.

---

## 4. Infrastructure Review

| Area | Finding | Evidence | Status |
| --- | --- | --- | --- |
| Database exposure | Prod Postgres `publicly_accessible = true` and SG open to `0.0.0.0/0:5432`, hardcoded password, `deletion_protection = false`, 1-day backups | `terraform/modules/rds/main.tf`, `terraform/envs/prod/main.tf` | **Fixed** |
| Network policy | `allow-all` ingress+egress in prod namespace → free lateral movement | `kubernetes/network-policy.yaml` | **Fixed** (default-deny + DNS) |
| CI/CD | Tests run with `\|\| true` (failures ignored); prod deploy on any `feature/*`; no approval | `.github/workflows/deploy.yml` | **Fixed** (tests gate, main-only, environment approval, dry-run) |
| GitOps | ArgoCD `Validate=false` with auto-sync + prune | `argocd/duopoly-prod.yaml` | **Fixed** (`Validate=true`) |
| Secrets | Live-style Stripe key in plaintext manifest | `kubernetes/billing-service.yaml` | **Fixed** (`secretKeyRef`) |
| Resource sizing | Workers request 50m CPU but limit 16 cores; 80 replicas | `kubernetes/agent-workers.yaml` | **Fixed** (right-sized 500m/1 core) |
| Gateway config | `LOG_LEVEL=debug`, `MAX_RETRIES=100` in prod | `kubernetes/llm-gateway.yaml` | **Fixed** |

The CI/CD pipeline was the highest-leverage infrastructure risk: it both shipped the broken code that caused the incidents *and* would re-ship it, because failing tests did not block deployment and feature branches could deploy straight to prod. Gating deploys on tests is the control that makes every other fix durable.

---

## 5. Observability Assessment

The platform measures **availability, not user impact**, which is why every incident coincided with green dashboards.

Documented blind spots (`monitoring/grafana-dashboard-notes.md`) line up exactly with the incidents:
- No retry-count panel → the retry storm was invisible (Incident 001/002)
- No token-cost-by-tenant panel → the bill spike was invisible until the cloud invoice arrived (Incident 002)
- No workflow queue-depth panel → backlog was invisible (Incident 001)
- No cross-tenant access anomaly panel → the leak had no detection (Incident 003)
- No connection-pool saturation panel → the vector connection leak (1,000 unclosed connections in the smoke run, now 0) had no signal

The SLOs (`docs/SLO.md`) self-identify the gaps: gateway SLO excludes provider latency and retries; workflow SLO ignores queue age; tenant-manager SLO ignores authorization correctness; billing SLO does not reconcile against provider invoices. **These are the right SLIs to build next.**

---

## 6. Fixes Applied in This Review

All changes are small and test-backed. Full suite: **8/8 passing** (was 0/8).

**Services:** tenant-scoped workflow lookup; tenant-scoped vector search with guaranteed connection close; durable, ordered, tenant-preserving audit flush; bounded gateway retries + circuit breaker + backoff; real header redaction; bounded sub-agent spawning; completion-token billing; gateway cost includes completion tokens; reject `alg:none` JWTs; fixed workflow queue-name mismatch.

**Infrastructure:** private encrypted RDS with deletion protection and longer backups; removed public DB ingress; default-deny network policy; CI gates on tests and restricts prod deploys to `main` with an approval environment and manifest dry-run; ArgoCD validation enabled; Stripe key moved to a secret; right-sized worker resources; production-safe gateway config.

---

## 7. Remaining Risks and Tradeoffs

- **JWT signatures are still not cryptographically verified.** I reject `alg:none` and missing signatures (closing the forge-any-tenant hole), but full JWKS signature verification is roadmap Phase 1. Until then, treat auth as shape-validated, not trust-validated.
- **Tenant isolation is fixed per-call, not centrally enforced.** The patches close the known leaks, but the architecture still relies on each service remembering the predicate. The durable fix is a shared, mandatory tenant-context middleware (roadmap Phase 1–2).
- **Circuit breaker state is in-process.** With 2+ gateway replicas, breaker state is per-pod. Acceptable as a first mitigation; a shared/coordinated breaker is a follow-up.
- **Network policy is default-deny with only DNS allowed.** Per-service allow rules must be added alongside each Deployment or traffic will be blocked — intentional, but requires the follow-up work noted in the file.
- **Smoke/unit coverage is shallow.** Tests pin the specific regressions; they are not a substitute for integration tests on the isolation and retry paths (roadmap).

I have intentionally left no failing tests. Where a fix is partial (JWT verification, central isolation, distributed breaker), it is called out above and scheduled rather than silently expanded — per the brief's preference for small, defensible fixes over broad rewrites.
