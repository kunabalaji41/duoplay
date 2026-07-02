EVENTS = []
BUFFER = []
FLUSH_THRESHOLD = 3


def record_event(actor_id, tenant_id, action, target_id, metadata=None):
    event = {
        "actor_id": actor_id,
        "tenant_id": tenant_id,
        "action": action,
        "target_id": target_id,
        "metadata": metadata or {},
    }
    BUFFER.append(event)
    if len(BUFFER) >= FLUSH_THRESHOLD:
        flush()
    return event


def flush():
    while BUFFER:
        event = BUFFER.pop(0)
        EVENTS.append(event)
    return EVENTS


if __name__ == "__main__":
    for index in range(5):
        record_event("user-1", "tenant-acme", "workflow.read", f"wf-{index}")
    print(flush())

