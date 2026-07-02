MAX_SUBAGENTS = 5


class AgentRuntime:
    def __init__(self):
        self.spawned_agents = []

    def create_subagent(self, parent_id, topic):
        agent_id = f"{parent_id}-sub-{len(self.spawned_agents)}"
        self.spawned_agents.append({"id": agent_id, "topic": topic})
        return agent_id

    def run(self, agent_id, task):
        confidence = 0
        spawned_this_run = 0
        while confidence < 95 and spawned_this_run < MAX_SUBAGENTS:
            self.create_subagent(agent_id, task)
            spawned_this_run += 1
            confidence += self.estimate_confidence(task)
        converged = confidence >= 95
        return {
            "agent_id": agent_id,
            "spawned": len(self.spawned_agents),
            "converged": converged,
        }

    def estimate_confidence(self, task):
        if "research" in task:
            return 0
        return 20


if __name__ == "__main__":
    runtime = AgentRuntime()
    print(runtime.run("agent-sales", "research market expansion"))

