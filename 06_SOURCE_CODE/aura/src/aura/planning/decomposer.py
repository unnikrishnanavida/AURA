"""Goal decomposition.

Orders a candidate task set into a dependency-valid execution sequence. The
decomposer is deterministic: identical input always yields identical output.
"""

from __future__ import annotations

from aura.foundation.errors import ValidationError
from aura.planning.models import Goal, Task


class GoalDecomposer:
    def decompose(self, goal: Goal, tasks: list[Task]) -> list[Task]:
        """Topologically order tasks honoring declared prerequisites."""
        del goal  # decomposition depends only on task dependencies
        by_name = {task.name: task for task in tasks}
        if len(by_name) != len(tasks):
            raise ValidationError("duplicate task names in goal decomposition")

        for task in tasks:
            missing = [p for p in task.prerequisites if p not in by_name]
            if missing:
                raise ValidationError(f"task {task.name!r} has unknown prerequisites {missing}")

        visited: set[str] = set()
        visiting: set[str] = set()
        ordered: list[Task] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise ValidationError(f"circular dependency between tasks near {name!r}")
            visiting.add(name)
            for prereq in by_name[name].prerequisites:
                visit(prereq)
            visiting.discard(name)
            visited.add(name)
            ordered.append(by_name[name])

        for task in tasks:
            visit(task.name)

        if len(ordered) != len(tasks):
            raise ValidationError("task decomposition produced an incomplete ordering")
        return ordered


__all__ = ["GoalDecomposer"]