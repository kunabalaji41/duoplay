# Incident 003: Cross-Tenant Workflow Visibility

Time: Wednesday 14:30

Customer report:

> I can see another tenant's workflow execution in our dashboard.

Symptoms:

- Tenant dashboard occasionally shows workflow IDs owned by other tenants.
- Support can reproduce with a copied workflow ID.
- Audit logs do not clearly show which tenant accessed the record.

Candidate tasks:

- Treat this as a critical security incident.
- Identify the missing tenant isolation.
- Provide a minimal fix.
- Define containment, notification, and audit reconstruction steps.

