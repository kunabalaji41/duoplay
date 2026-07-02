# 90-Day AgentOps Roadmap — Duopoly

**Role:** Head of AgentOps
**Operating principle:** contain first, then prevent, then mature. Trust user-impact signals over availability dashboards. Prefer small, reversible, test-backed changes.

This review already landed the emergency patches (8/8 tests passing, dangerous infra closed). The roadmap turns those point fixes into durable platform properties.

---

## Phase 0 — Containment (Days 0–7) — already substantially done in this review

Goal: stop active harm and preserve evidence.

- **Cross-tenant leak (Incident 003):** tenant predicate enforced on workflow lookup and vector search. *Remaining:* rotate any credentials seen in logs; run a blast-radius query over the exposure window using DB query logs + gateway logs (audit logs were lossy); declare severity and trigger the customer/compliance notification path.
- **Retry storm (Incidents 001/002):** retry budget capped at 3, circuit breaker on, sub-agent spawn ceiling. *Remaining:* set a temporary per-tenant request cap as a brownout lever.
- **Cost:** completion-token billing restored so the real bill is visible; capped retries cut worst-case amplification ~30x.
- **Infra:** public DB closed, secrets moved out of manifests, CI gates on tests.
- **Exit criteria:** no known active data-exposure path; bill trending back toward baseline; incident comms sent.

## Phase 1 — Stabilize and see clearly (Days 8–30)

Goal: make user impact observable and make isolation/auth structurally sound.

- **Observability (top priority — lowest readiness score):**
  - Build the five missing panels: retry rate, workflow queue depth/age, cost-per-tenant, cross-tenant access anomalies, connection-pool saturation.
  - Replace availability SLOs with impact-based SLIs from `docs/SLO.md`: queue age, end-to-end agent latency (incl. provider time), authorization-correctness, invoice reconciliation drift.
  - Alerting policy: page on user impact (queue age, cost-budget breach, cross-tenant anomaly); ticket on capacity/latency trends. Restructure `prometheus-rules.yaml` accordingly.
- **Auth hardening:** full JWT signature verification against provider JWKS (Phase 0 only rejects `alg:none`). Add audience/expiry/issuer checks.
- **Central tenant isolation:** introduce mandatory tenant-context middleware so isolation is enforced once, not re-implemented per call. Add a CI lint that fails any data-access function lacking a tenant predicate.
- **Audit durability:** move the audit buffer to a durable, append-only sink with retention sufficient for security investigations; add tenant-scoped query tooling.
- **Exit criteria:** dashboards reflect the three incidents had they recurred; no `alg:none` path; isolation enforced centrally with a CI guard.

## Phase 2 — Resilience and cost governance (Days 31–60)

Goal: the platform absorbs provider failures and bounds spend without human intervention.

- **Resilience:** shared/distributed circuit-breaker state across gateway replicas; backpressure and per-tenant concurrency limits; **idempotency keys** on agent actions to eliminate the duplicate-action class from Incident 001.
- **Autoscaling:** HPA/KEDA on workflow queue depth rather than CPU; validate honest requests/limits under load.
- **Cost governance:** per-tenant cost budgets with soft (alert) and hard (throttle) limits; **daily reconciliation** of internal usage vs provider invoices with drift alerts; cost attribution surfaced to tenants.
- **Delivery safety:** progressive delivery (canary/blue-green) via ArgoCD with automated rollback on SLO regression; sync windows.
- **Exit criteria:** simulated provider brownout degrades gracefully (no storm, bounded cost); reconciliation drift < agreed threshold.

## Phase 3 — Maturity and scale (Days 61–90)

Goal: prove the platform at scale and institutionalize the practices.

- **Scale validation:** load test to and beyond 500k workflows/day across 4 providers; capacity model and headroom targets.
- **Tenant isolation at the data layer:** evaluate row-level security / schema-per-tenant; per-tenant network policies.
- **Security posture:** secret scanning + rotation in CI, least-privilege K8s/cloud IAM, periodic access reviews; complete the per-service NetworkPolicy allow-list on top of the default-deny baseline.
- **Operational practice:** game days exercising the latency and security runbooks (both currently have gaps — no containment step, no brownout lever); blameless postmortems; on-call with impact-based paging.
- **Exit criteria:** documented capacity headroom; runbooks rehearsed and gap-free; production readiness score ≥ 8 across all five areas.

---

## Sequencing rationale

Isolation and the retry budget come first because they caused the live incidents. Observability is front-loaded in Phase 1 because **every incident here happened behind green dashboards** — without impact-based signals the team cannot safely move faster. Cost governance and resilience follow once the platform is observable, and scale/maturity work comes last because it is only meaningful on a foundation that is already secure, reliable, and measurable.

## How I would measure success at day 90

- Zero cross-tenant exposure incidents; isolation enforced centrally with a CI guard.
- Provider brownouts handled with bounded latency and bounded cost (no storm).
- Billing reconciles to provider invoices within tolerance; per-tenant budgets enforced.
- Mean time to *detect* user impact drops from "customer/cloud-invoice tells us" to minutes.
- Readiness scorecard ≥ 8/10 in every category, with observability no longer the laggard.
