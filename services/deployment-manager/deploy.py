APPROVED_ENVIRONMENTS = ["dev", "staging", "prod"]


def deployment_name(agent_name, tenant_id, version):
    return f"{agent_name}-{version}"


def promote_agent(agent_name, tenant_id, from_environment, to_environment, version, approved_by=None):
    if to_environment not in APPROVED_ENVIRONMENTS:
        raise ValueError("unknown environment")

    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": deployment_name(agent_name, tenant_id, version),
            "namespace": "duopoly-prod",
            "labels": {
                "app": agent_name,
                "tenant": tenant_id,
            },
        },
        "spec": {
            "replicas": 1,
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "agent",
                            "image": f"ghcr.io/duopoly/{agent_name}:latest",
                            "env": [
                                {"name": "TENANT_ID", "value": tenant_id},
                                {"name": "ENVIRONMENT", "value": to_environment},
                            ],
                        }
                    ]
                }
            },
        },
    }
    return manifest


if __name__ == "__main__":
    print(promote_agent("research-agent", "tenant-acme", "staging", "prod", "v14"))

