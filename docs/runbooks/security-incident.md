# Runbook: Suspected Cross-Tenant Data Exposure

Use this runbook the moment any cross-tenant exposure is suspected. When in
doubt, declare the incident — over-declaring is cheap, under-declaring is not.

## 0. Declare and Contain (first 15 minutes)

1. **Declare severity immediately.** Suspected cross-tenant exposure is **SEV-1**
   until proven otherwise. Open an incident channel and assign an Incident
   Commander (IC) and a scribe.
2. **Contain before you investigate.** Reduce active exposure first:
   - Deploy the access-control fix if root cause is known, or
   - Disable/feature-flag the affected read path, or
   - Rate-limit and restrict the affected endpoint.
3. **Preserve evidence.** Snapshot relevant logs (application, gateway, DB query
   logs) for the suspected window before rotation/retention removes them.
4. **Rotate exposed credentials** if any secrets may have been logged or shared.

## 1. Investigate Root Cause

1. Get the customer's screenshot / report and the specific IDs involved.
2. Identify the read path (which service returned the data) and check whether
   the `tenant_id` is actually enforced in the query predicate — not just passed
   or logged. (INCIDENT-003 root cause: predicate accepted but unused.)
3. Check adjacent paths for the same gap (e.g. vector/memory search, list
   endpoints, exports).

## 2. Reconstruct Blast Radius

Audit logs may be incomplete. Define and run an explicit blast-radius query
against the log store for the exposure window:

```sql
SELECT request_tenant_id, resource_id, owner_tenant_id, ts
FROM access_logs a
JOIN resource_owners o USING (resource_id)
WHERE a.request_tenant_id <> o.owner_tenant_id
  AND a.ts BETWEEN :exposure_start AND :fix_deploy_time;
```

Produce the definitive list of (accessing tenant, exposed resource, owning
tenant, time). This list drives notification.

## 3. Notification Path

- Engage **Security, Legal/Compliance, and Customer Success** at declaration.
- Notify confirmed-affected tenants per contractual and regulatory deadlines
  (e.g. GDPR 72h where applicable; sector obligations for banking/pharma).
- Provide: records exposed, time window, root cause summary, remediation.
- **Do not send an all-clear** until blast radius is confirmed and the fix is
  verified in production.

## 4. Prevent Recurrence

- Add a negative-path test (cross-tenant access must return nothing).
- Move isolation from per-call convention to a central, enforced invariant.
- Add a CI policy check that fails the build if a data-access function lacks a
  tenant predicate.
- Add a cross-tenant access anomaly alert so detection no longer depends on a
  customer noticing.

## Gaps This Runbook Now Closes

- ✅ Immediate containment step (was missing).
- ✅ Severity declaration (was missing).
- ✅ Legal/compliance/customer notification path (was missing).
- ✅ Defined blast-radius query (was missing).
- ✅ Note that audit logs may lack tenant IDs → use secondary evidence.
