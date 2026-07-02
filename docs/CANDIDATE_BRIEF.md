# Candidate Brief: Duopoly Platform

You have joined Duopoly as the incoming Head of AgentOps. Customers are reporting reliability problems, unexpected billing spikes, and one possible cross-tenant data exposure.

Your task is to review this repository as if it were a real production platform.

## Business Context

Duopoly lets enterprise customers build, deploy, and run AI agents. Customers include banks, pharma, logistics, and manufacturing organizations.

The platform runs:

- Agent workflows
- LLM calls
- Vector search
- Billing attribution
- Tenant-level quotas
- Kubernetes workloads
- Cloud database infrastructure
- Monitoring dashboards
- Authentication and audit services
- CI/CD promotion into production

## Current Incidents

Read the files in `duopoly/incidents/`.

You should assume all incident reports are based on real customer impact.

Some incidents have incomplete logs or misleading dashboards. Part of the exercise is deciding what evidence is trustworthy.

## Required Output

Submit:

1. Architecture review, maximum 10 pages.
2. Risk register:

   | Risk | Impact | Likelihood | Priority |
   | ---- | ------ | ---------- | -------- |

3. Production readiness score out of 10 for:

   - Security
   - Reliability
   - Scalability
   - Cost
   - Observability

4. Code or infrastructure fixes for the highest-priority issues.
5. A 90-day AgentOps roadmap.

Optional but recommended:

- Run `make -C duopoly test`.
- Add or update tests for your fixes.
- Explain any failures you intentionally leave unfixed.

## Rules

- You may edit any code or infrastructure files.
- Prefer small, defensible fixes over broad rewrites.
- Explain tradeoffs and remaining risks.
- Treat cross-tenant data exposure as a critical incident.
