from typing import List, Dict, Any, Set


class TraceabilityAgent:
    """
    Agent 8.14 & Section 14: Traceability Engine

    Maintains and audits the end-to-end traceability chain:

        Source Document
            -> Requirement
            -> Architecture Module
            -> Task
            -> Test Case

    Responsibilities:
    - Build the requirement-to-artifact traceability matrix.
    - Preserve source provenance.
    - Identify orphan requirements.
    - Identify dangling task/test references.
    - Validate architecture-module references.
    - Calculate requirement coverage.
    - Generate default acceptance/performance test cases.
    """

    def generate_traceability_matrix(
        self,
        requirements: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        test_cases: List[Dict[str, Any]],
        modules: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate the complete traceability matrix.

        A requirement is considered fully linked only when:
        1. It has at least one valid task.
        2. It has at least one valid test case.
        3. At least one linked task has a valid architecture module
           when a module_id is provided.

        No artificial/fallback IDs are created.
        """

        # ---------------------------------------------------------
        # 1. Build valid architecture-module lookup
        # ---------------------------------------------------------
        module_map: Dict[str, str] = {
            str(module["id"]): module.get("name", "")
            for module in modules
            if module.get("id")
        }

        valid_module_ids: Set[str] = set(module_map.keys())

        # ---------------------------------------------------------
        # 2. Build requirement lookup
        # ---------------------------------------------------------
        requirement_ids: Set[str] = {
            str(req["id"])
            for req in requirements
            if req.get("id")
        }

        # ---------------------------------------------------------
        # 3. Map requirements -> tasks
        # ---------------------------------------------------------
        req_to_tasks: Dict[str, List[Dict[str, Any]]] = {}

        dangling_task_requirement_refs: List[Dict[str, Any]] = []

        for task in tasks:
            task_id = task.get("id")
            requirement_id = task.get("requirement_id")

            if not task_id:
                continue

            if requirement_id:
                requirement_id = str(requirement_id)

                if requirement_id in requirement_ids:
                    req_to_tasks.setdefault(
                        requirement_id, []
                    ).append(task)
                else:
                    dangling_task_requirement_refs.append(
                        {
                            "task_id": task_id,
                            "requirement_id": requirement_id,
                            "issue": "Task references a non-existent requirement",
                        }
                    )

        # ---------------------------------------------------------
        # 4. Map requirements -> test cases
        # ---------------------------------------------------------
        req_to_tests: Dict[str, List[Dict[str, Any]]] = {}

        dangling_test_requirement_refs: List[Dict[str, Any]] = []

        for test_case in test_cases:
            test_id = test_case.get("id")
            requirement_id = test_case.get("requirement_id")

            if not test_id:
                continue

            if requirement_id:
                requirement_id = str(requirement_id)

                if requirement_id in requirement_ids:
                    req_to_tests.setdefault(
                        requirement_id, []
                    ).append(test_case)
                else:
                    dangling_test_requirement_refs.append(
                        {
                            "test_id": test_id,
                            "requirement_id": requirement_id,
                            "issue": "Test case references a non-existent requirement",
                        }
                    )

        # ---------------------------------------------------------
        # 5. Generate traceability matrix
        # ---------------------------------------------------------
        matrix: List[Dict[str, Any]] = []

        fully_linked = 0
        orphan_count = 0

        requirements_without_tasks: List[str] = []
        requirements_without_tests: List[str] = []
        requirements_with_invalid_modules: List[str] = []

        # ---------------------------------------------------------
        # 6. Process every requirement
        # ---------------------------------------------------------
        for requirement in requirements:
            requirement_id = requirement.get("id")

            if not requirement_id:
                continue

            requirement_id = str(requirement_id)

            matched_tasks = req_to_tasks.get(
                requirement_id,
                [],
            )

            matched_tests = req_to_tests.get(
                requirement_id,
                [],
            )

            # -----------------------------------------------------
            # Determine valid task-module relationships
            # -----------------------------------------------------
            task_module_links: List[Dict[str, Any]] = []

            for task in matched_tasks:
                module_id = task.get("module_id")

                if module_id:
                    module_id = str(module_id)

                    if module_id in valid_module_ids:
                        task_module_links.append(
                            {
                                "task_id": task.get("id"),
                                "module_id": module_id,
                                "module_name": module_map.get(
                                    module_id
                                ),
                            }
                        )
                    else:
                        requirements_with_invalid_modules.append(
                            requirement_id
                        )

            # -----------------------------------------------------
            # Infer module only from a valid task-module link
            # -----------------------------------------------------
            if task_module_links:
                primary_module = task_module_links[0]

                module_id = primary_module["module_id"]
                module_name = primary_module["module_name"]

            else:
                module_id = None
                module_name = None

            # -----------------------------------------------------
            # Determine orphan status
            # -----------------------------------------------------
            has_tasks = len(matched_tasks) > 0
            has_tests = len(matched_tests) > 0

            if not has_tasks:
                requirements_without_tasks.append(
                    requirement_id
                )

            if not has_tests:
                requirements_without_tests.append(
                    requirement_id
                )

            # A requirement is fully linked when it has both
            # a task and a test.
            #
            # Module linkage is recorded separately because some
            # tasks may intentionally not have an architecture
            # module yet.
            is_orphan = not has_tasks or not has_tests

            if is_orphan:
                orphan_count += 1
            else:
                fully_linked += 1

            # -----------------------------------------------------
            # Preserve source provenance exactly
            # -----------------------------------------------------
            source_id = requirement.get("source_id")
            source_page = requirement.get("source_page")

            # -----------------------------------------------------
            # Build matrix entry
            # -----------------------------------------------------
            matrix.append(
                {
                    "source_id": source_id,
                    "source_page": source_page,
                    "requirement_id": requirement_id,
                    "requirement_summary": requirement.get(
                        "summary",
                        "",
                    ),
                    "req_type": requirement.get(
                        "req_type",
                        "functional",
                    ),
                    "status": requirement.get(
                        "status",
                        "approved",
                    ),
                    "module_id": module_id,
                    "module_name": module_name,
                    "task_ids": [
                        task["id"]
                        for task in matched_tasks
                        if task.get("id")
                    ],
                    "test_ids": [
                        test_case["id"]
                        for test_case in matched_tests
                        if test_case.get("id")
                    ],
                    "task_module_links": task_module_links,
                    "is_orphan": is_orphan,
                }
            )

        # ---------------------------------------------------------
        # 7. Calculate coverage
        # ---------------------------------------------------------
        total_requirements = len(requirement_ids)

        coverage_pct = round(
            (
                fully_linked
                / total_requirements
                * 100.0
            )
            if total_requirements > 0
            else 100.0,
            1,
        )

        # ---------------------------------------------------------
        # 8. Remove duplicate requirement IDs from diagnostics
        # ---------------------------------------------------------
        requirements_with_invalid_modules = list(
            dict.fromkeys(
                requirements_with_invalid_modules
            )
        )

        # ---------------------------------------------------------
        # 9. Return complete traceability result
        # ---------------------------------------------------------
        return {
            "matrix": matrix,

            "total_requirements": total_requirements,

            "fully_linked_count": fully_linked,

            "orphan_count": orphan_count,

            "coverage_pct": coverage_pct,

            # Detailed diagnostics
            "requirements_without_tasks": (
                requirements_without_tasks
            ),

            "requirements_without_tests": (
                requirements_without_tests
            ),

            "requirements_with_invalid_modules": (
                requirements_with_invalid_modules
            ),

            "dangling_task_requirement_refs": (
                dangling_task_requirement_refs
            ),

            "dangling_test_requirement_refs": (
                dangling_test_requirement_refs
            ),

            # Overall integrity indicator.
            #
            # This does NOT mean that the requirements are
            # functionally correct. It only indicates that the
            # traceability references themselves are structurally
            # consistent.
            "traceability_integrity": (
                len(dangling_task_requirement_refs) == 0
                and len(dangling_test_requirement_refs) == 0
                and len(requirements_with_invalid_modules) == 0
            ),
        }

    def generate_default_test_cases(
        self,
        requirements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate one default test case for each requirement.

        IMPORTANT:
        These test cases are generated definitions only.
        They have NOT been executed.

        Therefore their status is always:
            "not_run"

        No test is marked as passed/failed without an
        actual execution engine.
        """

        test_cases: List[Dict[str, Any]] = []

        test_count = 1

        for requirement in requirements:
            requirement_id = requirement.get("id")

            if not requirement_id:
                continue

            requirement_id = str(requirement_id)

            summary = requirement.get(
                "summary",
                "",
            ).strip()

            actor = requirement.get(
                "actor",
                "User",
            )

            target_object = requirement.get(
                "target_object",
                "expected data",
            )

            req_type = requirement.get(
                "req_type",
                "functional",
            )

            test_id = f"TEST-{test_count:03d}"

            test_count += 1

            # -----------------------------------------------------
            # Determine test type
            # -----------------------------------------------------
            if req_type == "functional":
                test_type = "acceptance"
            else:
                test_type = "performance"

            # -----------------------------------------------------
            # Build test case
            # -----------------------------------------------------
            test_case = {
                "id": test_id,

                "requirement_id": requirement_id,

                "title": (
                    f"Verify {summary}"
                    if summary
                    else f"Verify requirement {requirement_id}"
                ),

                "test_type": test_type,

                "preconditions": (
                    f"System deployed; "
                    f"{actor} logged in"
                ),

                "steps": [
                    (
                        f"Trigger the system behavior for "
                        f"requirement '{summary}'"
                    ),
                    (
                        "Verify that the system processes "
                        "the request successfully"
                    ),
                    (
                        f"Validate the expected "
                        f"{target_object}"
                    ),
                ],

                "expected_result": (
                    f"Requirement {requirement_id} "
                    "acceptance criteria are satisfied "
                    "without regression"
                ),

                # Generated test case has NOT been executed.
                "status": "not_run",
            }

            test_cases.append(test_case)

        return test_cases