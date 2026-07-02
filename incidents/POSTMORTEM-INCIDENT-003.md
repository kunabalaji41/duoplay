# Postmortem — INCIDENT-003: Cross-Tenant Workflow Visibility

**Severity:** SEV-1 (confirmed cross-tenant data exposure)
**Status:** Mitigated — code fix deployed; notification and audit reconstruction in progress
**Authors:** Head of AgentOps
**Customers affected:** Potentially any of 250 tenants (regulated: banking, pharma, logistics, manufacturing)

> This is a blameless postmortem. The goal is to fix the system and the process, not to assign fault.

---

## 1. Summary

A tenant reported seeing another tenant's workflow execution in their dashboard. Support reproduced it by querying with a workflow ID belonging to a different tenant. Root cause: the workflow lookup accepted a `tenant_id` but did not include it in the query predicate, so any authenticated caller could read any workflow by ID. Two adjacent defects amplified impact and hindered investigation: vector/memory search was also not tenant-scoped, and the audit service was discarding the `tenant_id` field needed to reconstruct who accessed what.

## 2. Impact

- **Confidentiality breach** of workflow metadata across tenant boundaries. For regulated customers, workflow names alone (e.g. `bank-risk-review`, `trial-monitoring`) can be sensitive.
- Exposure is **deterministic**, not a race: anyone with a valid session and a target workflow ID could retrieve it. IDs are guessable/sequential in sample data (`wf-100`, `wf-200`, `wf-300`), raising enumeration risk.
- Detection came from a **customer report**, not internal monitoring — there was no cross-tenant access alert.

## 3. Timeline (UTC)

| Time | Event |
| --- | --- |
| Wed 14:30 | Customer reports seeing another tenant's workflow ID in their dashboard |
| Wed 14:45 | Support reproduces with a copied workflow ID → exposure confirmed |
| Wed 15:00 | SEV-1 declared; incident channel opened; IC assigned |
| Wed 15:20 | Root cause identified in `tenant-manager/db.py` (missing tenant predicate) |
| Wed 15:40 | Adjacent gaps found: vector search not tenant-scoped; audit drops `tenant_id` |
| Wed 16:10 | Code fix prepared and tested (tenant predicate + vector scoping + audit retention) |
| Wed 16:30 | Fix deployed; reproduction no longer possible |
| Wed → | Audit reconstruction, customer notification, and prevention work begin |

*(Times reflect the investigation sequence; adjust to the real clock when filing.)*

## 4. Root Cause

**Primary:** `services/tenant-manager/db.py` — the lookup was

```sql
SELECT * FROM workflows WHERE workflow_id = ?
```

The `tenant_id` was passed in and logged, but never used to filter. The matching Python loop checked only `workflow_id`.

**Contributing:**
- `services/vector-service/search.py` ranked documents across all tenants — the same isolation gap on the agent-memory retrieval path.
- `services/audit-service/audit.py` dropped `tenant_id` on flush, capped its buffer at 3 events (silently dropping the rest), and flushed in reverse order — so the audit trail could not answer "which tenant accessed this record."
- **Systemic:** tenant isolation was a per-call convention rather than a centrally enforced invariant (noted in `docs/ARCHITECTURE.md` as known debt). Any service that forgets the predicate leaks silently, with no shared guardrail.

## 5. Containment (immediate)

1. **Declare SEV-1** and open an incident channel with an Incident Commander. *(Was missing from the runbook — now added.)*
2. **Deploy the tenant predicate fix** so reproduction is no longer possible (done).
3. **Reduce enumeration exposure** until fully verified: consider non-sequential workflow IDs / opaque external IDs, and rate-limit lookup endpoints.
4. **Rotate** any credentials observed in logs (gateway previously logged headers).

## 6. Blast-Radius Reconstruction

Because audit logs were lossy during the exposure window, blast radius must be reconstructed from secondary evidence:

- **Application/gateway logs:** the lookup logged `{workflow_id, tenant_id}` on every call. Query for events where the **requesting** `tenant_id` does not own the returned `workflow_id`.
- **Database query logs** (if enabled) for the `workflows` table over the exposure window.
- Cross-reference against the workflow→owner mapping to produce the definitive list of (accessing tenant, exposed workflow, owning tenant) tuples.

Example reconstruction query (pseudo-SQL against the log store):

```sql
SELECT request_tenant_id, workflow_id, owner_tenant_id, ts
FROM access_logs a
JOIN workflow_owners o USING (workflow_id)
WHERE a.request_tenant_id <> o.owner_tenant_id
  AND a.ts BETWEEN :exposure_start AND :fix_deploy_time;
```

## 7. Notification

- **Internal:** Security, Legal/Compliance, and Customer Success engaged at SEV-1 declaration.
- **External:** notify confirmed-affected tenants per contractual and regulatory timelines (e.g. GDPR 72h where applicable; sector-specific obligations for banking/pharma). Provide the specific records exposed, the window, and remediation.
- Do **not** send an all-clear until blast-radius reconstruction is complete and the fix is verified in production.

## 8. Prevention (so it can't recur)

| Action | Type | Owner | When |
| --- | --- | --- | --- |
| Tenant predicate on workflow lookup | Fix (done) | AgentOps | Done |
| Tenant-scope vector search | Fix (done) | AgentOps | Done |
| Audit retains `tenant_id`, FIFO, durable | Fix (done) | AgentOps | Done |
| Negative-path tests (cross-tenant returns None) | Test (done) | AgentOps | Done |
| **Central tenant-context middleware** (enforce once) | Structural | Platform | Phase 1 |
| **CI policy check**: fail build if a data-access fn lacks a tenant predicate | Prevention | Platform | Phase 1 |
| Cross-tenant access **anomaly alert** | Detection | AgentOps | Phase 1 |
| Opaque/non-sequential workflow IDs | Hardening | Platform | Phase 2 |

## 9. Lessons Learned

- **What went well:** once reported, root cause was fast to find and the fix was small and test-backed.
- **What went wrong:** isolation relied on every developer remembering a convention; there was no detection; and the audit system failed exactly when it was needed most.
- **Where we got lucky:** detection depended on a customer noticing. Without the report, this could have run indefinitely.
- **Biggest systemic fix:** move tenant isolation from convention to enforced invariant (middleware + CI guard + detection), so a single forgotten predicate can never again become a breach.
