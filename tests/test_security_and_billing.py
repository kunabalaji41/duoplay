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


def unsigned_token(payload):
    header = {"alg": "none", "typ": "JWT"}

    def encode(value):
        raw = json.dumps(value).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{encode(header)}.{encode(payload)}."


class SecurityAndBillingTests(unittest.TestCase):
    def test_workflow_lookup_is_tenant_scoped(self):
        tenant_db = load_module("tenant_db", "services/tenant-manager/db.py")
        workflow = tenant_db.get_workflow_by_id("wf-200", "tenant-acme")
        self.assertIsNone(workflow)

    def test_unsigned_jwt_is_rejected(self):
        auth = load_module("auth", "services/auth-service/auth.py")
        token = unsigned_token({"tenant_id": "tenant-acme", "aud": "duopoly-api"})
        with self.assertRaises(PermissionError):
            auth.current_tenant(token)

    def test_completion_tokens_are_billed(self):
        billing = load_module("billing", "services/billing-service/billing.py")
        charge = billing.usage_charge("openai", prompt_tokens=1000, completion_tokens=9000)
        self.assertEqual(charge, 0.28)

    def test_audit_flush_preserves_tenant_and_order(self):
        audit = load_module("audit", "services/audit-service/audit.py")
        audit.EVENTS.clear()
        audit.BUFFER.clear()
        audit.record_event("user-1", "tenant-acme", "workflow.read", "wf-100")
        audit.record_event("user-2", "tenant-contoso", "workflow.read", "wf-200")
        events = audit.flush()
        self.assertIn("tenant_id", events[0])
        self.assertIn("tenant_id", events[1])
        self.assertEqual(events[0]["tenant_id"], "tenant-acme")
        self.assertEqual(events[1]["tenant_id"], "tenant-contoso")


if __name__ == "__main__":
    unittest.main()
