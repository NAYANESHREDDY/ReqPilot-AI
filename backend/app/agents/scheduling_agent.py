import networkx as nx
from typing import List, Dict, Any


class SchedulingAgent:
    """
    Agent 8.13 & Section 28: Scheduling & Dependency Agent

    Responsibilities:
    - Construct a directed dependency graph.
    - Validate dependency references.
    - Detect dependency cycles.
    - Produce a dependency-respecting execution order.
    - Allocate tasks into capacity-bounded sprints.
    - Never fabricate or silently discard dependency information.
    """

    def schedule_tasks(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        sprint_capacity_points: int = 25,
    ) -> Dict[str, Any]:

        if sprint_capacity_points <= 0:
            raise ValueError("sprint_capacity_points must be greater than zero")

        G = nx.DiGraph()

        # ---------------------------------------------------------
        # 1. Validate and add task nodes
        # ---------------------------------------------------------
        task_dict = {}

        for task in tasks:
            task_id = task.get("id")

            if not task_id:
                continue

            if task_id in task_dict:
                raise ValueError(f"Duplicate task ID detected: {task_id}")

            task_dict[task_id] = task

            points = task.get("story_points", 3)

            try:
                points = int(points)
            except (TypeError, ValueError):
                points = 3

            if points <= 0:
                points = 1

            task["story_points"] = points

            G.add_node(
                task_id,
                points=points,
                title=task.get("title", ""),
            )

        # ---------------------------------------------------------
        # 2. Validate and add dependency edges
        # ---------------------------------------------------------
        invalid_dependencies = []
        accepted_dependencies = []

        for dep in dependencies:

            depends_on = dep.get("depends_on_task_id")
            task_id = dep.get("task_id")

            if not depends_on or not task_id:
                invalid_dependencies.append({
                    "dependency": dep,
                    "reason": "Missing task ID"
                })
                continue

            if depends_on not in task_dict:
                invalid_dependencies.append({
                    "dependency": dep,
                    "reason": f"Unknown dependency task: {depends_on}"
                })
                continue

            if task_id not in task_dict:
                invalid_dependencies.append({
                    "dependency": dep,
                    "reason": f"Unknown dependent task: {task_id}"
                })
                continue

            if depends_on == task_id:
                invalid_dependencies.append({
                    "dependency": dep,
                    "reason": "Self-dependency is not allowed"
                })
                continue

            if G.has_edge(depends_on, task_id):
                continue

            G.add_edge(depends_on, task_id)
            accepted_dependencies.append(dep)

        # ---------------------------------------------------------
        # 3. Detect cycles
        # ---------------------------------------------------------
        original_is_acyclic = nx.is_directed_acyclic_graph(G)

        cycles_detected = []
        cycles_resolved = []

        if not original_is_acyclic:

            # Find all simple cycles rather than only one cycle.
            cycles_detected = list(nx.simple_cycles(G))

            # Deterministically break cycles.
            #
            # For each cycle, remove the last dependency edge.
            # This allows scheduling to continue while explicitly
            # reporting what was changed.
            for cycle in cycles_detected:

                if len(cycle) < 2:
                    continue

                source = cycle[-1]
                target = cycle[0]

                if G.has_edge(source, target):

                    G.remove_edge(source, target)

                    cycles_resolved.append(
                        f"{source} -> {target}"
                    )

        # ---------------------------------------------------------
        # 4. Validate final graph
        # ---------------------------------------------------------
        final_is_acyclic = nx.is_directed_acyclic_graph(G)

        if not final_is_acyclic:
            raise ValueError(
                "Unable to resolve dependency cycles safely."
            )

        # ---------------------------------------------------------
        # 5. Dependency-respecting execution order
        # ---------------------------------------------------------
        execution_order = list(nx.topological_sort(G))

        # ---------------------------------------------------------
        # 6. Sprint allocation
        # ---------------------------------------------------------
        sprints = []

        current_sprint_num = 1
        current_sprint_points = 0
        current_sprint_tasks = []

        for task_id in execution_order:

            task = task_dict[task_id]
            points = task["story_points"]

            # Oversized task:
            # Put it into its own sprint rather than silently
            # violating sprint capacity.
            if points > sprint_capacity_points:

                if current_sprint_tasks:
                    sprints.append({
                        "sprint_name": f"Sprint {current_sprint_num}",
                        "total_points": current_sprint_points,
                        "task_ids": current_sprint_tasks,
                    })

                    current_sprint_num += 1
                    current_sprint_points = 0
                    current_sprint_tasks = []

                task["sprint_name"] = f"Sprint {current_sprint_num}"

                sprints.append({
                    "sprint_name": f"Sprint {current_sprint_num}",
                    "total_points": points,
                    "task_ids": [task_id],
                    "over_capacity": True,
                })

                current_sprint_num += 1

                continue

            # Start a new sprint when capacity would be exceeded.
            if (
                current_sprint_tasks
                and current_sprint_points + points
                > sprint_capacity_points
            ):
                sprints.append({
                    "sprint_name": f"Sprint {current_sprint_num}",
                    "total_points": current_sprint_points,
                    "task_ids": current_sprint_tasks,
                    "over_capacity": False,
                })

                current_sprint_num += 1
                current_sprint_points = 0
                current_sprint_tasks = []

            sprint_name = f"Sprint {current_sprint_num}"

            task["sprint_name"] = sprint_name

            current_sprint_tasks.append(task_id)
            current_sprint_points += points

        # ---------------------------------------------------------
        # 7. Persist final sprint
        # ---------------------------------------------------------
        if current_sprint_tasks:
            sprints.append({
                "sprint_name": f"Sprint {current_sprint_num}",
                "total_points": current_sprint_points,
                "task_ids": current_sprint_tasks,
                "over_capacity": False,
            })

        # ---------------------------------------------------------
        # 8. Return complete scheduling result
        # ---------------------------------------------------------
        return {
            "is_valid_dag": original_is_acyclic,
            "schedule_valid": final_is_acyclic,

            "cycles_detected": [
                cycle for cycle in cycles_detected
            ],

            "cycles_resolved": cycles_resolved,

            "invalid_dependencies": invalid_dependencies,

            "execution_order": execution_order,

            "sprints": sprints,

            "scheduled_tasks": list(task_dict.values()),
        }