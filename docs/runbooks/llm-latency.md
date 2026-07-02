# Runbook: LLM Provider Latency

## Symptoms

- Customer-visible agent delays.
- Workflow queue depth / queue age increasing.
- Gateway fallback and retry rate increasing.
- Cloud/provider egress and cost climbing.

## 0. Stop the Amplification First

Restarting pods or scaling workers does **not** stop a retry storm — it can make
it worse by adding load and cost. Reduce amplification before scaling:

1. **Clamp the retry budget.** Confirm `MAX_RETRIES` is small (≤ 3) and the
   circuit breaker is enabled (`CIRCUIT_BREAKER_ENABLED = True`). If a config
   regression raised it, roll back the gateway config now.
2. **Trip the breaker on the sick provider.** Let the breaker route around the
   failing provider (e.g. OpenAI) instead of retrying it every round.
3. **Tenant brownout lever.** If a few tenants are driving the load, apply a
   temporary per-tenant concurrency/request cap to protect the platform
   (graceful degradation for the noisy tenants, availability for everyone else).

## 1. Diagnose

1. Check **retry rate** and **per-provider failure rate** panels (not just pod
   health). A green availability dashboard does not mean users are healthy.
2. Check **workflow queue depth and age** — rising queue age is the real
   user-impact signal.
3. Check **cost-per-tenant / egress** to catch a cost blowup early.

## 2. Mitigate

1. With retries clamped and the breaker open, latency-bound requests fail fast
   instead of stacking up behind a slow provider.
2. Only **then** consider scaling workers, and only if the queue is backed up by
   legitimate (non-retry) load.
3. Ensure agent actions are **idempotent** so retried/duplicated work does not
   double-execute (the "duplicate agent actions" symptom in INCIDENT-001).

## 3. Recover and Verify

1. Confirm queue age returns to baseline and retry rate normalizes.
2. Re-enable any tenant that was browned out.
3. Capture provider status for the postmortem.

## 4. Prevent

- Keep the retry budget + circuit breaker as enforced defaults (and assert them
  in tests).
- Add HPA/KEDA driven by queue depth, not CPU.
- Add the retry-rate, queue-age, and cost-per-tenant panels + alerts.

## Gaps This Runbook Now Closes

- ✅ Restarting pods does not stop retry amplification → clamp retries first.
- ✅ Scaling workers can worsen provider load/cost → scale only after clamping.
- ✅ Documented retry-budget switch (`MAX_RETRIES` / breaker).
- ✅ Tenant-level brownout procedure.
