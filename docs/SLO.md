# Production SLOs (Revised)

This revises the original SLO draft. The guiding principle: **measure user
impact, not component availability.** Every incident in this case study happened
while the old SLIs were green, because they tracked pod uptime and HTTP 200 rate
rather than what customers actually experienced (slow agents, wrong bills,
leaked data).

## Original SLOs and why they were insufficient

| Service | Original SLI | Problem |
| --- | --- | --- |
| LLM Gateway | HTTP 200 rate | A request that succeeds after a retry storm is "200" but slow and expensive |
| Workflow Engine | Worker pod availability | Pods can be up while the queue backs up for hours |
| Tenant Manager | Request success | Success ≠ correct; a cross-tenant read is a "successful" request |
| Billing Service | Invoice job success | Job can succeed while under-counting vs the provider invoice |
| Vector Service | Pod CPU < 80% | CPU says nothing about search latency or tenant correctness |

## Revised SLOs (impact-based)

| Service | SLI (what the user feels) | Target | Why |
| --- | --- | ---: | --- |
| LLM Gateway | End-to-end successful response latency **including** provider + retries, p95 | < 8s, 99% | Captures the latency users actually saw in INCIDENT-001 |
| LLM Gateway | Retry amplification ratio (provider calls ÷ client requests) | < 1.5 | Detects retry storms directly (INCIDENT-001/002) |
| Workflow Engine | **Queue age** (time from enqueue to pickup), p95 | < 30s | Backlog is the real symptom; pod uptime hid it |
| Agent Runtime | Workflow completion rate (no duplicate execution) | 99.9% | Targets the "duplicate agent actions" symptom |
| Tenant Manager | **Authorization correctness** (cross-tenant reads) | 0 (any breach = SEV-1) | Correctness, not just success (INCIDENT-003) |
| Billing Service | Invoice **reconciliation drift** vs provider invoice | < 1% | Detects under-counting (INCIDENT-002) |
| Vector Service | Search latency p95 + connection-pool saturation | < 200ms / < 80% | Real UX + the connection-leak class of bug |

## Page vs Ticket policy

The point of an SLO is to decide **who gets woken up**. The test: *is a customer
being harmed right now, or is this a trend we should fix during business hours?*

**Page an engineer (immediate, customer harm in progress):**
- Authorization-correctness SLO breached → **any** cross-tenant access (SEV-1).
- Queue age p95 > 30s and rising → workflows stalling for customers.
- Retry amplification ratio > 1.5 → active retry storm (latency + cost).
- Cost-budget hard limit breached for a tenant or globally → runaway spend.
- Gateway p95 latency SLO breached for 5m → agents unusable.

**Open a ticket (trend / capacity, fix in hours/days, no immediate harm):**
- Reconciliation drift between 0.5–1% → investigate before it grows.
- Vector search latency degrading but under target → capacity planning.
- Single pod restart / transient blip with no SLO impact.
- CPU/memory trending toward limits without user-facing symptoms.

**Explicitly do NOT page on:**
- A single pod down while the service SLO is still met (the old `up == 0`
  page caused noise without signal).
- HTTP 200 rate alone — it does not reflect latency, cost, or correctness.

## Error budgets

Each SLO has an error budget (e.g. gateway latency 99% → 1% budget/month).
Burning budget fast (e.g. >2% in an hour) escalates from ticket to page. When a
budget is exhausted, freeze risky changes for that service until it recovers —
this ties the SLOs back to the CI/CD delivery controls.
