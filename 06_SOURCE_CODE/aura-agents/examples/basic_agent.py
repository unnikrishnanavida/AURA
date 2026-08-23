"""Basic agent example: build an agent with a controlled tool and complete a goal.

Run with:  python examples/basic_agent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura_agent import dsl
from aura_agent.tools import SchemaField, Tool


def build_agent():
    """A filesystem writer agent with an explicit permission grant."""
    def _write(inputs, *, context):
        return {"path": inputs["path"], "written": True, "completed": True}

    write_tool = Tool(
        name="filesystem.write",
        description="write a string to a path",
        input_schema={
            "path": SchemaField(name="path", type=str, required=True),
            "content": SchemaField(name="content", type=str, required=True),
        },
        capability="filesystem.write",
        permissions=("filesystem:write",),
        handler=_write,
        timeout_s=5,
    )

    def _finalize(_inputs, *, context):
        return {"completed": True, "ok": True}

    finalize_tool = Tool(
        name="tools.finalize",
        description="finalize the task",
        input_schema={},
        capability="tools.finalize",
        permissions=(),
        handler=_finalize,
        timeout_s=5,
    )

    return (
        dsl.AgentBuilder(name="example-basic")
        .with_tool(write_tool)
        .with_tool(finalize_tool)
        .allow(action="filesystem.*", resource="filesystem.*")
        .allow(action="tools.*", resource="*")
        .with_capability("filesystem.write")
        .with_capability("tools.finalize")
        .build()
    )


def main() -> None:
    agent = build_agent()
    print(f"Agent {agent.agent_id} ready.")

    # 1. execute a single action through the guarded pipeline
    from aura_agent.contracts.ids import ActionId
    from aura_agent.execution_bridge import ExecutionRequest

    result = agent.execute_action(
        ExecutionRequest(
            action_id=ActionId.new(),
            tool_name="filesystem.write",
            capability="filesystem.write",
            agent_id=agent.agent_id,
            inputs={"path": "/tmp/example.txt", "content": "hello"},
        )
    )
    print(f"action executed: success={result.success}")

    # 2. run a goal through the cognitive loop (uses the no-input finalize
    #    tool, so the deterministic planner can bind and execute it)
    goal = agent.create_goal(
        description="finalize the task",
        success_criteria=["completed == True"],
    )
    outcome = agent.run_goal(goal=goal, capabilities=["tools.finalize"])
    print(f"goal outcome: success={outcome.success}, iterations={outcome.iterations}")
    print(
        "goal status:",
        agent.components.goal_engine.get(goal.id).status.value,
    )

    # 3. telemetry
    print("telemetry:", agent.components.telemetry.snapshot(str(agent.agent_id)))


if __name__ == "__main__":
    main()