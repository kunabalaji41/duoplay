# Duopoly Risk Register

Priority scale: **P0** (critical, act now) · **P1** (high, this quarter) · **P2** (medium, planned).
Status reflects work done in this review.

| # | Risk | Impact | Likelihood | Priority | Evidence | Proposed Fix | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Cross-tenant workflow data exposure | Critical (regulated tenants: banks, pharma; breach + compliance) | High | **P0** | `tenant-manager/db.py`: lookup filters on `workflow_id` only, `tenant_id` unused; reproducible by support | Add `tenant_id` to query predicate; central tenant-context enforcement | **Fixed** (predicate added; central middleware on roadmap) |
| 2 | Cross-tenant vector/memory exposure | Critical (agent memory leakage between tenants) | High | **P0** | `vector-service/search.py`: ranks all `DOCUMENTS` regardless of tenant | Filter candidates by `tenant_id` before ranking | **Fixed** |
| 3 | Audit log unusable for investigation | Critical (cannot prove blast radius or notify correctly) | High | **P0** | `audit-service/audit.py`: drops `tenant_id`, caps buffer at 3, reverses order | Preserve `tenant_id`, FIFO order, durable flush | **Fixed** |
| 4 | Retry storm during provider latency | High (latency, queue backlog, duplicate agent actions) | High | **P0** | `llm-gateway/app.py`: `MAX_RETRIES=100` × 4 providers, breaker disabled, no backoff | Bounded retry budget + circuit breaker + backoff | **Fixed** |
| 5 | Retry/cost amplification (bill spike) | High ($8k→$58k/day; ~30x worst-case amplification) | High | **P0** | Incident 002; same retry path as #4; egress spike | Retry budget (#4) + per-tenant cost budgets + quotas | **Partly fixed** (budget capped; tenant quotas on roadmap) |
| 6 | Public production database | Critical (direct data theft / ransom) | High | **P0** | `terraform`: `publicly_accessible=true`, SG `0.0.0.0/0:5432`, hardcoded password | Private subnet, restrict CIDR, secret-managed password, encryption | **Fixed** |
| 7 | CI/CD ships broken code to prod | High (root cause of incident propagation) | High | **P0** | `deploy.yml`: tests `\|\| true`; deploy on `feature/*`; no approval | Gate on tests; main-only; protected environment; dry-run | **Fixed** |
| 8 | Unsigned/forgeable JWTs accepted | Critical (impersonate any tenant) | Medium | **P0** | `auth-service/auth.py`: `alg:none` returns payload | Reject `alg:none`; verify signature against JWKS | **Partly fixed** (`alg:none` rejected; full verify on roadmap) |
| 9 | Secrets in source / manifests | High (credential compromise) | High | **P1** | `billing-service.yaml` plaintext Stripe key; gateway logs headers; `redact_headers` no-op | `secretKeyRef`; redact sensitive headers; rotate exposed keys | **Fixed** (rotation is an ops action) |
| 10 | Billing under-counting vs provider invoice | High (revenue leakage, hidden cost signal) | High | **P1** | `billing.py`: charges prompt tokens only | Charge prompt + completion tokens; reconcile vs invoice | **Fixed** (reconciliation job on roadmap) |
| 11 | Unbounded sub-agent spawning | High (worker saturation, runaway cost) | Medium | **P1** | `agent-runtime/runtime.py`: spawn loop, `estimate_confidence("research")==0` | Hard spawn ceiling + convergence guard | **Fixed** |
| 12 | Flat / permissive network policy | High (lateral movement after compromise) | Medium | **P1** | `network-policy.yaml`: allow-all ingress+egress | Default-deny + explicit per-service allows | **Fixed** (baseline; per-service rules to add) |
| 13 | Unsafe GitOps sync | Medium (invalid/drifted manifests auto-applied) | Medium | **P1** | `argocd`: `Validate=false`, auto-sync+prune | Enable validation; consider sync windows | **Fixed** |
| 14 | Unrealistic K8s resource limits | Medium (noisy-neighbor, scheduling/cost issues) | Medium | **P2** | `agent-workers.yaml`: 50m request / 16-core limit, 80 replicas | Right-size requests/limits; HPA on queue depth | **Fixed** (sizing); HPA on roadmap |
| 15 | Observability blind to user impact | High (every incident had green dashboards) | High | **P1** | `prometheus-rules.yaml`, `grafana-dashboard-notes.md`, `SLO.md` | Add retry/queue-depth/cost-per-tenant/anomaly panels; impact-based SLOs | **Open** (roadmap Phase 1) |
| 16 | Workflow queue-name mismatch | Medium (submitted work never consumed) | Medium | **P2** | `worker.py`: submits to `agent-workflow-prod`, workers consume `agent-workflows-prod` | Single source of truth for queue name | **Fixed** |
| 17 | Verbose prod logging | Low/Medium (cost, possible PII in logs) | Medium | **P2** | `llm-gateway.yaml`: `LOG_LEVEL=debug` | Set `info`; structured logging with redaction | **Fixed** |

## Prioritization rationale

P0s cluster into two themes: **tenant isolation** (#1, #2, #3, #6, #8) and **retry-driven reliability/cost** (#4, #5), plus the **delivery control** (#7) that lets broken code reach prod. Per the brief, tenant data exposure was treated first. The retry budget (#4) is the highest-leverage reliability fix because it simultaneously addresses Incidents 001 and 002. CI/CD gating (#7) is the control that prevents regression of everything else.
