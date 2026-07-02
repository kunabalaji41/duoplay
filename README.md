# Duopoly Platform — DevOps / AgentOps Case Study Submission

Submission for the Duopoly Platform case study. I reviewed the platform as the
incoming Head of AgentOps, identified the highest-risk failures behind the three
live incidents, fixed the highest-priority issues with small test-backed patches,
hardened the infrastructure, and produced the required deliverables.

## TL;DR

The three incidents are not independent. A single unbounded-retry defect caused
both the latency backlog (INCIDENT-001) and the cloud bill spike (INCIDENT-002);
billing under-counting hid the cost; and a missing tenant predicate caused the
cross-tenant data leak (INCIDENT-003), while a lossy audit log would have blocked
the investigation. Every incident happened behind green dashboards, because the
platform measured availability instead of user impact.

All fixes are backed by tests: **26 tests pass** (8 provided + 18 added).

## How to Validate

```bash
# Full test suite (was 0/8 passing, now 26/26)
python -m unittest discover -s tests -v

# Smoke targets
python services/billing-service/billing.py     # -> 0.28 (completion tokens billed)
python services/tenant-manager/db.py            # -> None (cross-tenant read blocked)
python services/vector-service/search.py        # -> {'open_connections': 0} (no leak)
```

(`make smoke` / `make test` also work where `make` is available.)

## Deliverables

| # | Deliverable | File |
| --- | --- | --- |
| 1 | Architecture review (max 10 pages) | [`docs/ARCHITECTURE_REVIEW.md`](docs/ARCHITECTURE_REVIEW.md) |
| 2 | Risk register (impact / likelihood / priority) | [`docs/RISK_REGISTER.md`](docs/RISK_REGISTER.md) |
| 3 | Production readiness scores (5 areas) | [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) |
| 4 | Code / infrastructure patches | see "Fixes" below |
| 5 | 90-day AgentOps roadmap | [`docs/AGENTOPS_90_DAY_ROADMAP.md`](docs/AGENTOPS_90_DAY_ROADMAP.md) |

### Supporting artifacts

- Incident postmortem: [`incidents/POSTMORTEM-INCIDENT-003.md`](incidents/POSTMORTEM-INCIDENT-003.md)
- Runbooks (gaps filled): [`docs/runbooks/`](docs/runbooks/)
- Revised SLOs with page-vs-ticket policy: [`docs/SLO.md`](docs/SLO.md)
- Regression tests for the fixes: [`tests/test_fixes_regression.py`](tests/test_fixes_regression.py)

## Fixes Applied

### Security (P0)
- **Cross-tenant workflow leak** — `tenant-manager/db.py` now filters on `tenant_id`.
- **Cross-tenant vector search** — `vector-service/search.py` scoped to the tenant; connections released.
- **Audit integrity** — `audit-service/audit.py` keeps `tenant_id`, FIFO order, and no dropped events.
- **Auth** — `auth-service/auth.py` rejects unsigned (`alg:none`) tokens.
- **Infra** — private encrypted RDS (no public `0.0.0.0/0`), default-deny network policy, Stripe key moved to a secret.

### Reliability & Cost (P0/P1)
- **Retry storm** — `llm-gateway/app.py`: retries 100 -> 3, circuit breaker enabled, backoff added, headers redacted.
- **Runaway agents** — `agent-runtime/runtime.py`: hard sub-agent spawn ceiling.
- **Billing under-counting** — `billing-service/billing.py`: completion tokens now billed.
- **Queue mismatch** — `workflow-engine/worker.py`: consistent queue name.

### Delivery
- **CI/CD** — `.github/workflows/deploy.yml`: tests gate deploys, prod restricted to `main` with an approval environment.
- **GitOps** — `argocd/duopoly-prod.yaml`: manifest validation enabled.

## Key Tradeoffs / Remaining Risks

- JWT signature verification against JWKS is scheduled (Phase 1); only `alg:none` is rejected so far.
- Tenant isolation is fixed per-call; central enforcing middleware is on the roadmap.
- Circuit-breaker state is in-process; a shared breaker is a follow-up.

See the architecture review and roadmap for the full reasoning.
