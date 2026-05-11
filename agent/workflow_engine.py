"""
Workflow execution engine for Power BI agent.

Manages step-by-step execution of workflow plans with error handling,
retries, state management, and validation.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from server.models import WorkflowExecutionState, ToolExecutionResult
from .tool_router import ToolRouter


class WorkflowEngine:
    """Orchestrates workflow execution."""

    def __init__(self, tool_router: ToolRouter):
        """
        Initialize workflow engine.

        Args:
            tool_router: Tool router for MCP execution
        """
        self.tool_router = tool_router
        self.execution_states: Dict[str, WorkflowExecutionState] = {}

    def execute_workflow(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        on_step_complete=None,
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow plan.

        Args:
            workflow_id: Unique workflow identifier
            steps: Ordered list of workflow steps
            on_step_complete: Optional callback after each step

        Returns:
            Workflow execution result
        """
        # Initialize execution state
        execution = WorkflowExecutionState(
            workflow_id=workflow_id,
            current_step_id="",
            steps_completed=0,
            total_steps=len(steps),
            status="running",
            start_time=datetime.now(),
        )

        self.execution_states[workflow_id] = execution

        # Store step results for parameter substitution
        step_results: Dict[str, Any] = {}

        try:
            # Execute each step
            for idx, step in enumerate(steps):
                step_id = step.get("step_id", f"step_{idx}")
                execution.current_step_id = step_id

                # Check dependencies
                depends_on = step.get("depends_on", [])
                if not self._check_dependencies(depends_on, step_results):
                    execution.errors.append(f"Dependency failed for step {step_id}")
                    execution.status = "failed"
                    break

                # Execute step with retry logic
                result = self._execute_step_with_retry(
                    step, step_results
                )

                # Store result
                step_results[step_id] = result

                # Update execution state
                if result.get("success"):
                    execution.steps_completed += 1
                    execution.step_results[step_id] = ToolExecutionResult(
                        success=True,
                        tool_name=step.get("tool_name", ""),
                        message=result.get("message", ""),
                        data=result.get("data"),
                    )
                else:
                    execution.errors.append(
                        result.get("error", f"Step {step_id} failed")
                    )
                    execution.status = "failed"
                    break

                # Callback hook
                if on_step_complete:
                    on_step_complete(execution)

            # Final status
            if execution.status == "running":
                execution.status = "completed"

        except Exception as e:
            execution.status = "failed"
            execution.errors.append(f"Workflow error: {str(e)}")

        finally:
            execution.end_time = datetime.now()
            self.execution_states[workflow_id] = execution

        return self._format_result(execution, step_results)

    def _execute_step_with_retry(
        self,
        step: Dict[str, Any],
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a step with retry logic.

        Args:
            step: Workflow step
            previous_results: Results from previous steps

        Returns:
            Execution result
        """
        max_retries = step.get("max_retries", 3)
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Route step to tool
                result = self.tool_router.route_step(step, previous_results)

                if result.get("success"):
                    return result

                # Check if should retry
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = min(2 ** retry_count, 10)  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    return result

            except Exception as e:
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(2 ** retry_count)
                else:
                    return {
                        "success": False,
                        "error": str(e),
                    }

    def _check_dependencies(
        self,
        depends_on: List[str],
        step_results: Dict[str, Any],
    ) -> bool:
        """
        Check if all dependencies have been met.

        Args:
            depends_on: List of dependency step IDs
            step_results: Completed step results

        Returns:
            True if all dependencies met
        """
        if not depends_on:
            return True

        for dep_id in depends_on:
            if dep_id not in step_results:
                return False

            dep_result = step_results[dep_id]
            if not dep_result.get("success"):
                return False

        return True

    def _format_result(
        self,
        execution: WorkflowExecutionState,
        step_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format workflow execution result.

        Args:
            execution: Execution state
            step_results: All step results

        Returns:
            Formatted result
        """
        duration = (
            (execution.end_time - execution.start_time).total_seconds()
            if execution.end_time
            else 0
        )

        return {
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "success": execution.status == "completed" and len(execution.errors) == 0,
            "steps_completed": execution.steps_completed,
            "total_steps": execution.total_steps,
            "duration_seconds": duration,
            "errors": execution.errors,
            "step_results": step_results,
        }

    def get_execution_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current execution status of a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Execution status
        """
        execution = self.execution_states.get(workflow_id)

        if not execution:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}",
            }

        duration = (
            (execution.end_time - execution.start_time).total_seconds()
            if execution.end_time
            else (datetime.now() - execution.start_time).total_seconds()
        )

        return {
            "workflow_id": workflow_id,
            "status": execution.status,
            "current_step": execution.current_step_id,
            "steps_completed": execution.steps_completed,
            "total_steps": execution.total_steps,
            "progress_percent": (execution.steps_completed / execution.total_steps * 100)
            if execution.total_steps > 0
            else 0,
            "duration_seconds": duration,
            "errors": execution.errors,
        }

    def rollback_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Rollback changes from a failed workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Rollback result
        """
        execution = self.execution_states.get(workflow_id)

        if not execution:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}",
            }

        # Call rollback tool
        rollback_result = self.tool_router.route_step(
            {
                "tool_name": "rollback_changes",
                "tool_params": {},
                "step_id": "rollback",
            },
            {},
        )

        return {
            "success": rollback_result.get("success", False),
            "message": "Workflow rolled back",
            "workflow_id": workflow_id,
        }

    def pause_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Pause an executing workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Pause result
        """
        execution = self.execution_states.get(workflow_id)

        if not execution:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}",
            }

        if execution.status == "running":
            execution.status = "paused"
            return {"success": True, "message": "Workflow paused"}

        return {
            "success": False,
            "error": f"Cannot pause workflow in {execution.status} state",
        }

    def resume_workflow(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Resume a paused workflow.

        Args:
            workflow_id: Workflow identifier
            steps: Workflow steps

        Returns:
            Execution result
        """
        execution = self.execution_states.get(workflow_id)

        if not execution:
            return {
                "success": False,
                "error": f"Workflow not found: {workflow_id}",
            }

        if execution.status != "paused":
            return {
                "success": False,
                "error": f"Cannot resume workflow in {execution.status} state",
            }

        # Resume from current step
        remaining_steps = steps[execution.steps_completed:]
        return self.execute_workflow(workflow_id, remaining_steps)

    def get_workflow_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get history of recent workflows.

        Args:
            limit: Maximum number of workflows to return

        Returns:
            Workflow history
        """
        workflows = list(self.execution_states.values())
        sorted_workflows = sorted(
            workflows, key=lambda w: w.start_time, reverse=True
        )[:limit]

        return {
            "count": len(sorted_workflows),
            "workflows": [
                {
                    "workflow_id": w.workflow_id,
                    "status": w.status,
                    "steps_completed": w.steps_completed,
                    "total_steps": w.total_steps,
                    "start_time": w.start_time.isoformat(),
                    "end_time": w.end_time.isoformat() if w.end_time else None,
                    "error_count": len(w.errors),
                }
                for w in sorted_workflows
            ],
        }
