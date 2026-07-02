# Duopoly Architecture

Duopoly is organized as a set of independently deployed services.

## Request Path

1. Tenant dashboard or SDK sends an agent request.
2. Tenant Manager resolves tenant, plan, and workflow metadata.
3. Workflow Engine schedules long-running execution.
4. Agent Runtime creates plans and tool calls.
5. LLM Gateway routes provider requests.
6. Vector Service retrieves memory context.
7. Billing Service records token, storage, workflow, and agent usage.
8. Audit Service records security-sensitive operations.
9. Deployment Manager promotes agent versions to Kubernetes.
10. Monitoring stack collects operational signals.

## Operational Expectations

- Tenant isolation must be enforced on every read and write path.
- LLM provider failures must be isolated by timeout, retry budget, circuit breaker, and backpressure.
- Workflow queues must be observable and isolated by workload type.
- Billing must match provider invoices.
- Kubernetes requests and limits must represent realistic workload behavior.
- Cloud databases must be private and recoverable.
- Authentication must reject unsigned or weakly signed tokens.
- Audit logging must be durable enough for security investigations.

## Trust Boundaries

- Public API to LLM Gateway and Tenant Manager.
- Tenant dashboard to workflow metadata APIs.
- Agent Runtime to tool execution and deployment APIs.
- Deployment Manager to Kubernetes cluster credentials.
- Billing events to customer invoices.
- Audit events to incident response and compliance evidence.

## Known Technical Debt Areas

- Several services use in-memory examples instead of real adapters.
- CI validates syntax but not policy.
- Monitoring checks availability more than user impact.
- Tenant context is passed manually instead of enforced centrally.
