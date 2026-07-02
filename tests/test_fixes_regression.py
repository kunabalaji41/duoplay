"""Additional regression tests for the fixes applied in this review."""

import base64
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _b64(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")


def make_token(payload, alg="HS256", signature="sig"):
    header = {"alg": alg, "typ": "JWT"}
    return f"{_b64(header)}.{_b64(payload)}.{signature}"


class TenantIsolationTests(unittest.TestCase):
    def setUp(self):
        self.db = load_module("tenant_db", "services/tenant-manager/db.py")

    def test_owner_can_read_own_workflow(self):
        wf = self.db.get_workflow_by_id("wf-100", "tenant-acme")
        self.assertIsNotNone(wf)
        self.assertEqual(wf["tenant_id"], "tenant-acme")

    def test_other_tenant_cannot_read_workflow(self):
        self.assertIsNone(self.db.get_workflow_by_id("wf-100", "tenant-contoso"))
        self.assertIsNone(self.db.get_workflow_by_id("wf-300", "tenant-acme"))

    def test_list_is_scoped_to_tenant(self):
        workflows = self.db.list_tenant_workflows("tenant-acme")
        self.assertTrue(workflows)
        self.assertTrue(all(w["tenant_id"] == "tenant-acme" for w in workflows))


class VectorIsolationTests(unittest.TestCase):
    def setUp(self):
        self.vector = load_module("vector", "services/vector-service/search.py")
        self.vector.CONNECTIONS.clear()

    def test_search_only_returns_calling_tenant_documents(self):
        results = self.vector.search("tenant-contoso", [0.2, 0.1, 0.4])
        self.assertTrue(results)
        self.assertTrue(all(r["tenant_id"] == "tenant-contoso" for r in results))

    def test_connections_are_released_under_load(self):
        for _ in range(100):
            self.vector.search("tenant-acme", [0.2, 0.1, 0.4])
        self.assertEqual(len(self.vector.CONNECTIONS), 0)


class AuthHardeningTests(unittest.TestCase):
    def setUp(self):
        self.auth = load_module("auth", "services/auth-service/auth.py")

    def test_valid_signed_token_returns_tenant(self):
        token = make_token({"tenant_id": "tenant-acme", "aud": "duopoly-api"})
        self.assertEqual(self.auth.current_tenant(token), "tenant-acme")

    def test_wrong_audience_is_rejected(self):
        token = make_token({"tenant_id": "tenant-acme", "aud": "someone-else"})
        with self.assertRaises(PermissionError):
            self.auth.current_tenant(token)

    def test_missing_signature_is_rejected(self):
        token = make_token({"tenant_id": "tenant-acme", "aud": "duopoly-api"}, signature="")
        with self.assertRaises(PermissionError):
            self.auth.current_tenant(token)

    def test_none_algorithm_is_rejected(self):
        token = make_token({"tenant_id": "tenant-acme", "aud": "duopoly-api"}, alg="none", signature="")
        with self.assertRaises(PermissionError):
            self.auth.current_tenant(token)


class AuditDurabilityTests(unittest.TestCase):
    def test_burst_preserves_all_events_in_order_with_tenant(self):
        audit = load_module("audit", "services/audit-service/audit.py")
        audit.EVENTS.clear()
        audit.BUFFER.clear()
        tenants = ["tenant-acme", "tenant-contoso", "tenant-pharma", "tenant-acme", "tenant-contoso"]
        for i, tenant in enumerate(tenants):
            audit.record_event(f"user-{i}", tenant, "workflow.read", f"wf-{i}")
        audit.flush()
        self.assertEqual(len(audit.EVENTS), len(tenants))
        self.assertEqual([e["tenant_id"] for e in audit.EVENTS], tenants)
        self.assertEqual([e["target_id"] for e in audit.EVENTS], [f"wf-{i}" for i in range(len(tenants))])


class GatewayContainmentTests(unittest.TestCase):
    def setUp(self):
        self.gateway = load_module("gateway", "services/llm-gateway/app.py")

    def test_retry_budget_and_breaker_constants(self):
        self.assertLessEqual(self.gateway.MAX_RETRIES, 3)
        self.assertTrue(self.gateway.CIRCUIT_BREAKER_ENABLED)

    def test_chat_is_bounded_when_all_providers_fail(self):
        calls = {"n": 0}

        def always_fail(provider, prompt):
            calls["n"] += 1
            raise TimeoutError("down")

        self.gateway.call_provider = always_fail
        self.gateway.RETRY_BACKOFF_BASE = 0
        with self.assertRaises(RuntimeError):
            self.gateway.chat({"prompt": "hello world", "headers": {}})
        self.assertLessEqual(calls["n"], self.gateway.MAX_RETRIES * len(self.gateway.PROVIDERS))

    def test_sensitive_headers_redacted_cookie(self):
        headers = self.gateway.redact_headers({"cookie": "session=abc", "traceparent": "00-x"})
        self.assertEqual(headers["cookie"], "[REDACTED]")
        self.assertEqual(headers["traceparent"], "00-x")

    def test_estimate_cost_includes_completion_tokens(self):
        cost = self.gateway.estimate_cost(1000, 9000, "openai")
        self.assertAlmostEqual(cost, (1000 + 9000) * 0.00001)


class AgentRuntimeBoundTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module("runtime", "services/agent-runtime/runtime.py")

    def test_research_task_terminates_within_spawn_ceiling(self):
        runtime = self.module.AgentRuntime()
        result = runtime.run("agent-x", "research market expansion")
        self.assertLessEqual(result["spawned"], self.module.MAX_SUBAGENTS)
        self.assertFalse(result["converged"])

    def test_convergent_task_converges(self):
        runtime = self.module.AgentRuntime()
        result = runtime.run("agent-y", "summarize report")
        self.assertTrue(result["converged"])
        self.assertLessEqual(result["spawned"], self.module.MAX_SUBAGENTS)


class BillingCompletionTests(unittest.TestCase):
    def setUp(self):
        self.billing = load_module("billing", "services/billing-service/billing.py")

    def test_completion_tokens_billed_anthropic(self):
        charge = self.billing.usage_charge("anthropic", 1000, 9000)
        self.assertAlmostEqual(charge, 1000 * 0.000012 + 9000 * 0.00004)

    def test_monthly_invoice_sums_completion(self):
        total = self.billing.monthly_invoice([
            {"provider": "openai", "prompt_tokens": 1000, "completion_tokens": 9000},
            {"provider": "gemini", "prompt_tokens": 500, "completion_tokens": 500},
        ])
        expected = round(
            (1000 * 0.00001 + 9000 * 0.00003) + (500 * 0.000006 + 500 * 0.000018),
            2,
        )
        self.assertEqual(total, expected)


if __name__ == "__main__":
    unittest.main()
