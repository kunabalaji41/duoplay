WORKFLOWS = [
    {"tenant_id": "tenant-acme", "workflow_id": "wf-100", "name": "bank-risk-review"},
    {"tenant_id": "tenant-contoso", "workflow_id": "wf-200", "name": "factory-maintenance"},
    {"tenant_id": "tenant-pharma", "workflow_id": "wf-300", "name": "trial-monitoring"},
]


def get_workflow_by_id(workflow_id, tenant_id):
    query = "SELECT * FROM workflows WHERE workflow_id = ? AND tenant_id = ?"
    print({"query": query, "workflow_id": workflow_id, "tenant_id": tenant_id})

    for workflow in WORKFLOWS:
        if workflow["workflow_id"] == workflow_id and workflow["tenant_id"] == tenant_id:
            return workflow
    return None


def list_tenant_workflows(tenant_id):
    return [workflow for workflow in WORKFLOWS if workflow["tenant_id"] == tenant_id]


if __name__ == "__main__":
    print(get_workflow_by_id("wf-200", "tenant-acme"))

