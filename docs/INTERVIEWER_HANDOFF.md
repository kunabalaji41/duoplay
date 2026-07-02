# Interviewer Handoff

Use this file to run the Duopoly case study.

## What to Give the Candidate

Share:

- `README.md`
- `duopoly/docs/`
- `duopoly/incidents/`
- `duopoly/services/`
- `duopoly/platform/`
- `duopoly/tests/`
- `duopoly/Makefile`

Do not share:

- `duopoly/evaluator/`

## Suggested Prompt

You are the incoming Head of AgentOps for Duopoly. Customers are reporting LLM latency, a cloud bill spike, and possible cross-tenant workflow visibility. Review the repository, identify the most important risks, fix the highest-priority issues, and explain your 90-day plan.

## Time Boxes

| Format | Duration | Expected Output |
| --- | ---: | --- |
| Live screen | 90 minutes | Investigation, prioritization, 1-2 fixes |
| Senior take-home | 3-4 hours | Review, risk register, tests, top fixes |
| Staff case study | 1 day | Operating plan, deeper fixes, roadmap |

## Commands

```bash
make -C duopoly smoke
make -C duopoly test
```

`make test` should fail initially. The failures are part of the challenge.

## Evaluation Focus

- Does the candidate prioritize tenant data exposure first?
- Do they connect retry behavior to queue backlog and cost?
- Do they distrust green dashboards when user impact exists?
- Do they identify weak CI/CD production controls?
- Do they produce small, defensible patches?
- Do they explain containment, blast radius, and prevention?

