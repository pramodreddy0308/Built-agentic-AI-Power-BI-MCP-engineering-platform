"""
Main Power BI Agent orchestrator.

Coordinates planning, execution, and validation for autonomous Power BI modifications.
This is the main entry point for the agentic system.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from server.config import OPENAI_API_KEY, OPENAI_MODEL
from server.metadata_tools import MetadataTools
from server.validator import ValidatorTools
from .planner_agent import PlannerAgent
from .tool_router import ToolRouter
from .workflow_engine import WorkflowEngine


class PowerBIAgent:
    """
    Main autonomous Power BI Agent.

    Orchestrates AI planning, MCP tool execution, and workflow management
    for intelligent Power BI project modifications.
    """

    def __init__(self, pbip_root: Path, api_key: Optional[str] = None):
        """
        Initialize Power BI Agent.

        Args:
            pbip_root: Root path of PBIP project
            api_key: OpenAI API key (uses OPENAI_API_KEY env if not provided)

        Raises:
            ValueError: If API key not provided and not in environment
        """
        self.pbip_root = Path(pbip_root)

        # Get API key from parameter or centralized config
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key required")

        # Initialize tools
        self.metadata_tools = MetadataTools(self.pbip_root)
        self.validator_tools = ValidatorTools(self.pbip_root)

        # Initialize MCP components
        self.tool_router = ToolRouter(None)  # MCP client would be injected
        self.planner = PlannerAgent(self.api_key, self.tool_router, model=OPENAI_MODEL)
        self.workflow_engine = WorkflowEngine(self.tool_router)

        print("[OK] Power BI Agent initialized")
        print(f"  PBIP Root: {self.pbip_root}")
        print(f"  Model: {OPENAI_MODEL}")

    def process_request(
        self,
        user_request: str,
        auto_execute: bool = False,
        collect_context: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a user request end-to-end.

        Args:
            user_request: User's natural language request
            auto_execute: Whether to automatically execute the plan
            collect_context: Whether to collect report context

        Returns:
            Processing result containing plan and execution status
        """
        print(f"\n{'='*70}")
        print(f"Processing Request:")
        print(f"  {user_request}")
        print(f"{'='*70}\n")

        # PHASE 1: Collect Context
        if collect_context:
            print("PHASE 1: Collecting Report Context...")
            context = self._collect_context()
            print(f"  [OK] Collected metadata: {len(context.get('available_pages', []))} pages, "
                  f"{len(context.get('available_measures', []))} measures\n")
        else:
            context = {}

        # PHASE 2: Generate Plan
        print("PHASE 2: AI Planning...")
        try:
            plan = self.planner.plan_workflow(user_request, context)
            print(f"  [OK] Generated plan: {plan.plan_id}")
            print(f"  [OK] Steps: {len(plan.steps)}")
            print(f"  [OK] Reasoning: {plan.reasoning[:100]}...")

            # Validate plan
            validation = self.planner.validate_plan(plan)
            if not validation["is_valid"]:
                print(f"  [ERROR] Plan validation failed:")
                for issue in validation["issues"]:
                    print(f"    - {issue}")
                return {
                    "success": False,
                    "error": "Plan validation failed",
                    "plan": plan,
                    "validation": validation,
                }

            print(f"  [OK] Plan validated\n")

        except Exception as e:
            print(f"  [ERROR] Planning failed: {e}\n")
            return {
                "success": False,
                "error": f"Planning failed: {str(e)}",
            }

        # PHASE 3: Execute Plan
        if auto_execute:
            print("PHASE 3: Executing Workflow...")
            try:
                execution_result = self._execute_plan(plan)

                if execution_result["success"]:
                    print(f"  [OK] Workflow completed successfully")
                    print(f"  [OK] Steps completed: {execution_result['steps_completed']}/{execution_result['total_steps']}")
                    print(f"  [OK] Duration: {execution_result['duration_seconds']:.2f}s\n")
                else:
                    print(f"  [ERROR] Workflow failed")
                    if execution_result.get("errors"):
                        for error in execution_result["errors"]:
                            print(f"    - {error}")
                    print()

                return {
                    "success": execution_result["success"],
                    "plan": plan,
                    "execution": execution_result,
                }

            except Exception as e:
                print(f"  [ERROR] Execution failed: {e}\n")
                return {
                    "success": False,
                    "error": f"Execution failed: {str(e)}",
                    "plan": plan,
                }

        else:
            print("PHASE 3: Plan Ready (auto-execute disabled)")
            print(f"  To execute, call execute_plan() with the plan\n")

            return {
                "success": True,
                "plan": plan,
                "execution": None,
                "message": "Plan generated and validated. Ready for execution.",
            }

    def execute_plan(self, plan) -> Dict[str, Any]:
        """
        Execute a workflow plan.

        Args:
            plan: WorkflowPlan to execute

        Returns:
            Execution result
        """
        return self._execute_plan(plan)

    def _execute_plan(self, plan) -> Dict[str, Any]:
        """
        Execute a workflow plan.

        Args:
            plan: WorkflowPlan

        Returns:
            Execution result
        """
        steps_data = [
            {
                "step_id": step.step_id,
                "step_name": step.step_name,
                "tool_name": step.tool_name,
                "tool_params": step.tool_params,
                "depends_on": step.depends_on,
                "max_retries": step.max_retries,
            }
            for step in plan.steps
        ]

        return self.workflow_engine.execute_workflow(plan.plan_id, steps_data)

    def _collect_context(self) -> Dict[str, Any]:
        """
        Collect report context for planning.

        Returns:
            Context dictionary
        """
        context = {}

        try:
            # Get pages
            pages_result = self.metadata_tools.list_pages()
            context["available_pages"] = [p.get("display_name", p.get("page_name")) 
                                         for p in pages_result.get("pages", [])]

            # Get tables
            tables_result = self.metadata_tools.list_tables()
            context["available_tables"] = [t.get("table_name") 
                                          for t in tables_result.get("tables", [])]

            # Get measures
            measures_result = self.metadata_tools.list_measures()
            context["available_measures"] = [m.get("measure_name") 
                                            for m in measures_result.get("measures", [])]

            # Get report summary
            summary = self.metadata_tools.get_report_summary()
            context["report_summary"] = summary

        except Exception as e:
            print(f"Warning: Error collecting context: {e}")

        return context

    def interactive_mode(self):
        """
        Run agent in interactive mode for continuous requests.
        """
        print("\n" + "="*70)
        print("Power BI Agentic AI System - Interactive Mode")
        print("="*70)
        print("Enter your Power BI modification requests.")
        print("Type 'exit' to quit.\n")

        while True:
            try:
                user_request = input("📊 Request: ").strip()

                if user_request.lower() == "exit":
                    print("Goodbye!")
                    break

                if not user_request:
                    continue

                # Process request
                result = self.process_request(user_request, auto_execute=True)

                # Display result
                if result.get("success"):
                    print("\n[OK] Request completed successfully!")
                else:
                    print(f"\n[ERROR] Request failed: {result.get('error', 'Unknown error')}")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def validate_report(self) -> Dict[str, Any]:
        """
        Validate the current report state.

        Returns:
            Validation result
        """
        print("\nValidating report...")
        result = self.validator_tools.validate_report()
        print(f"  Pages: {result['pages_count']}")
        print(f"  Visuals: {result['visuals_count']}")
        print(f"  Measures: {result['measures_count']}")

        if result["errors"]:
            print(f"  [ERROR] Errors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"    - {error}")

        if result["warnings"]:
            print(f"  ⚠ Warnings: {len(result['warnings'])}")
            for warning in result["warnings"]:
                print(f"    - {warning}")

        return result

    def get_report_summary(self) -> Dict[str, Any]:
        """
        Get report summary information.

        Returns:
            Report summary
        """
        return self.metadata_tools.get_report_summary()

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.

        Returns:
            Agent information
        """
        return {
            "pbip_root": str(self.pbip_root),
            "model": "GPT-4 Turbo",
            "capabilities": [
                "Inspect PBIP structure (pages, visuals, measures)",
                "Create and modify DAX measures",
                "Add KPI cards and other visuals",
                "Replace visual types",
                "Reorganize layouts",
                "Apply themes",
                "Validate reports",
                "Commit changes to git",
            ],
            "mcp_tools_available": len(self.tool_router.tool_catalog),
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import sys

    # Initialize agent
    pbip_path = Path(os.getcwd())
    try:
        agent = PowerBIAgent(pbip_path)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Show agent info
    info = agent.get_agent_info()
    print(f"\nAgent Info:")
    for key, value in info.items():
        if isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
        else:
            print(f"  {key}: {value}")

    # Get report summary
    print("\nReport Summary:")
    summary = agent.get_report_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Validate report
    print("\n" + "="*70)
    agent.validate_report()

    # Run interactive mode
    print("\n" + "="*70)
    agent.interactive_mode()
