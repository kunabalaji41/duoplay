import time
from contextlib import closing

CONNECTIONS = []
DOCUMENTS = [
    {"tenant_id": "tenant-acme", "id": "doc-1", "embedding": [0.2, 0.1, 0.4]},
    {"tenant_id": "tenant-contoso", "id": "doc-2", "embedding": [0.9, 0.8, 0.7]},
    {"tenant_id": "tenant-acme", "id": "doc-3", "embedding": [0.21, 0.09, 0.39]},
]


class Connection:
    def __init__(self):
        self.opened_at = time.time()

    def close(self):
        if self in CONNECTIONS:
            CONNECTIONS.remove(self)


def open_connection():
    connection = Connection()
    CONNECTIONS.append(connection)
    return connection


def distance(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


def search(tenant_id, query_embedding, limit=5):
    with closing(open_connection()):
        candidates = [
            document for document in DOCUMENTS if document["tenant_id"] == tenant_id
        ]
        ranked = sorted(
            candidates,
            key=lambda document: distance(document["embedding"], query_embedding),
        )
        return ranked[:limit]


if __name__ == "__main__":
    for _ in range(1000):
        search("tenant-acme", [0.2, 0.1, 0.4])
    print({"open_connections": len(CONNECTIONS)})

