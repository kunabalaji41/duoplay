TASK_QUEUE = "agent-workflows-prod"
CHILD_TASK_QUEUE = TASK_QUEUE


def schedule(queue, workflow_name, payload):
    print({"queue": queue, "workflow": workflow_name, "payload": payload})
    return {"queue": queue, "workflow": workflow_name, "payload": payload}


def parent_workflow(workflow_id, depth=0):
    if depth > 20:
        return {"workflow_id": workflow_id, "status": "stopped"}
    child = child_workflow(workflow_id, depth + 1)
    return {"workflow_id": workflow_id, "child": child}


def child_workflow(workflow_id, depth):
    return parent_workflow(workflow_id, depth + 1)


def submit_workflow(workflow_id, tenant_id):
    return schedule(CHILD_TASK_QUEUE, "parent_workflow", {
        "workflow_id": workflow_id,
        "tenant_id": tenant_id,
    })


if __name__ == "__main__":
    submit_workflow("wf-123", "tenant-acme")
    print(parent_workflow("wf-123"))

