import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReliabilityTests(unittest.TestCase):
    def test_gateway_retry_budget_is_bounded(self):
        gateway = load_module("gateway", "services/llm-gateway/app.py")
        self.assertLessEqual(gateway.MAX_RETRIES, 3)
        self.assertTrue(gateway.CIRCUIT_BREAKER_ENABLED)

    def test_gateway_redacts_authorization_headers(self):
        gateway = load_module("gateway", "services/llm-gateway/app.py")
        headers = gateway.redact_headers({
            "authorization": "Bearer secret",
            "x-api-key": "sk-secret",
            "traceparent": "00-test",
        })
        self.assertEqual(headers["authorization"], "[REDACTED]")
        self.assertEqual(headers["x-api-key"], "[REDACTED]")
        self.assertEqual(headers["traceparent"], "00-test")

    def test_agent_runtime_has_spawn_limit(self):
        runtime_module = load_module("runtime", "services/agent-runtime/runtime.py")
        self.assertTrue(hasattr(runtime_module, "MAX_SUBAGENTS"))
        self.assertLessEqual(runtime_module.MAX_SUBAGENTS, 5)

    def test_vector_search_is_tenant_scoped_and_closes_connections(self):
        vector = load_module("vector", "services/vector-service/search.py")
        vector.CONNECTIONS.clear()
        results = vector.search("tenant-acme", [0.9, 0.8, 0.7])
        self.assertTrue(all(result["tenant_id"] == "tenant-acme" for result in results))
        self.assertEqual(len(vector.CONNECTIONS), 0)


if __name__ == "__main__":
    unittest.main()
