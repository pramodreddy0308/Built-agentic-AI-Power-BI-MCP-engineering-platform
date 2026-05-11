"""
AI Planner Agent using OpenAI GPT-4.

Analyzes user requests and generates detailed workflow execution plans
that leverage MCP tools to modify Power BI PBIP projects.
"""

import json
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from server.models import WorkflowPlan, WorkflowStep
from .prompts import PLANNER_SYSTEM_PROMPT
from .tool_router import ToolRouter


class PlannerAgent:
    """AI agent that generates execution plans."""

    def __init__(self, api_key: str, tool_router: ToolRouter):
        """
        Initialize planner agent.

        Args:
            api_key: OpenAI API key
            tool_router: Tool router for tool information
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
        self.tool_router = tool_router
        self.system_prompt = PLANNER_SYSTEM_PROMPT

    def plan_workflow(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowPlan:
        """
        Generate a workflow plan for a user request.

        Args:
            user_request: User's natural language request
            context: Optional context (metadata, current state, etc.)

        Returns:
            WorkflowPlan containing steps and reasoning
        """
        # Build context information
        context_str = self._build_context_string(context)

        # Build planning prompt
        planning_prompt = f"""USER REQUEST:
{user_request}

CONTEXT:
{context_str}

Your task is to generate a detailed, step-by-step workflow plan to accomplish this request.

Output your plan as a JSON object with this structure:
{{
    "plan_id": "plan_XXXXXXXX",
    "goal": "User's objective",
    "reasoning": "Explanation of your approach",
    "steps": [
        {{
            "step_id": "step_1",
            "step_name": "Human-readable step description",
            "tool_name": "mcp_tool_name",
            "tool_params": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "depends_on": [],
            "retry_count": 0,
            "max_retries": 3
        }}
    ],
    "estimated_duration_minutes": 5
}}

IMPORTANT RULES:
1. Each step must use a REAL MCP tool from the available tools
2. Parameters must be specific and complete
3. Steps must be in correct order with proper dependencies
4. Always inspect before modifying
5. Always validate after modifications
6. Always commit changes to git when complete
7. Handle missing components gracefully"""

        try:
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": planning_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # Extract response
            response_text = response.choices[0].message.content

            # Parse JSON from response
            plan_dict = self._extract_json_from_response(response_text)

            # Convert to WorkflowPlan model
            plan = self._dict_to_workflow_plan(plan_dict)

            return plan

        except Exception as e:
            print(f"Error generating plan: {e}")
            raise

    def refine_plan(
        self,
        original_plan: WorkflowPlan,
        feedback: str,
    ) -> WorkflowPlan:
        """
        Refine an existing plan based on feedback.

        Args:
            original_plan: Original workflow plan
            feedback: User feedback or issues with plan

        Returns:
            Refined workflow plan
        """
        refinement_prompt = f"""You previously generated this workflow plan:

Goal: {original_plan.goal}
Steps: {len(original_plan.steps)}

USER FEEDBACK:
{feedback}

Please revise the plan addressing the feedback. Output the complete revised plan as JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refinement_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content
            plan_dict = self._extract_json_from_response(response_text)
            refined_plan = self._dict_to_workflow_plan(plan_dict)

            return refined_plan

        except Exception as e:
            print(f"Error refining plan: {e}")
            raise

    def validate_plan(
        self,
        plan: WorkflowPlan,
        tool_catalog: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate a workflow plan for feasibility.

        Args:
            plan: Workflow plan to validate
            tool_catalog: Tool catalog for validation

        Returns:
            Validation report
        """
        issues = []
        warnings = []

        # Check each step
        for idx, step in enumerate(plan.steps):
            # Validate tool exists
            tool_name = step.tool_name
            tool_info = self.tool_router.get_tool_info(tool_name)

            if not tool_info.get("success"):
                issues.append(f"Step {idx+1}: Invalid tool '{tool_name}'")
                continue

            # Validate parameters
            tool_params = step.tool_params
            required_params = [
                p for p in tool_info.get("parameters", [])
                if not p.endswith("?")
            ]

            for required in required_params:
                if required not in tool_params:
                    issues.append(
                        f"Step {idx+1}: Missing parameter '{required}' for tool '{tool_name}'"
                    )

        # Check dependencies
        step_ids = {step.step_id for step in plan.steps}
        for step in plan.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    issues.append(f"Step {step.step_id}: Unknown dependency '{dep}'")

        # Check for validation steps
        has_validation = any("validate" in step.tool_name for step in plan.steps)
        if not has_validation:
            warnings.append("Plan has no validation steps")

        # Check for commit step
        has_commit = any("git_commit" in step.tool_name for step in plan.steps)
        if not has_commit:
            warnings.append("Plan has no git commit step")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "steps_count": len(plan.steps),
        }

    def suggest_alternatives(
        self,
        user_request: str,
        current_plan: WorkflowPlan,
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative approaches to accomplish the request.

        Args:
            user_request: User's request
            current_plan: Current plan

        Returns:
            List of alternative approaches
        """
        alternatives_prompt = f"""Given this user request:
{user_request}

And this current plan with {len(current_plan.steps)} steps,

Suggest 2-3 alternative approaches that could accomplish the same goal.

For each alternative:
1. Describe the approach in 1-2 sentences
2. List the tools that would be used
3. Estimate the complexity (simple, moderate, complex)
4. Note pros and cons

Format as JSON array of objects with keys: approach, tools, complexity, pros, cons"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert advisor helping optimize Power BI workflows.",
                    },
                    {"role": "user", "content": alternatives_prompt},
                ],
                temperature=0.8,
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content
            alternatives = self._extract_json_from_response(response_text)

            if isinstance(alternatives, list):
                return alternatives
            else:
                return []

        except Exception as e:
            print(f"Error suggesting alternatives: {e}")
            return []

    def _build_context_string(self, context: Optional[Dict[str, Any]]) -> str:
        """
        Build context string for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context string
        """
        if not context:
            return "No additional context provided."

        context_parts = []

        if "available_pages" in context:
            pages = context["available_pages"]
            context_parts.append(f"Available Pages: {', '.join(pages)}")

        if "available_measures" in context:
            measures = context["available_measures"]
            context_parts.append(f"Available Measures: {', '.join(measures[:5])}{'...' if len(measures) > 5 else ''}")

        if "available_tables" in context:
            tables = context["available_tables"]
            context_parts.append(f"Available Tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")

        if "report_summary" in context:
            summary = context["report_summary"]
            context_parts.append(f"Report has {summary.get('pages_count', 0)} pages, "
                               f"{summary.get('visuals_count', 0)} visuals, "
                               f"{summary.get('measures_count', 0)} measures")

        return "\n".join(context_parts) if context_parts else "No additional context provided."

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.

        Args:
            response_text: LLM response

        Returns:
            Extracted JSON as dictionary
        """
        # Try to find JSON in response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: Try entire response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            print("Warning: Could not parse JSON from response")
            return {}

    def _dict_to_workflow_plan(self, plan_dict: Dict[str, Any]) -> WorkflowPlan:
        """
        Convert dictionary to WorkflowPlan model.

        Args:
            plan_dict: Dictionary representation

        Returns:
            WorkflowPlan model instance
        """
        steps = []

        for step_dict in plan_dict.get("steps", []):
            step = WorkflowStep(
                step_id=step_dict.get("step_id", f"step_{len(steps)}"),
                step_name=step_dict.get("step_name", ""),
                tool_name=step_dict.get("tool_name", ""),
                tool_params=step_dict.get("tool_params", {}),
                depends_on=step_dict.get("depends_on", []),
                retry_count=step_dict.get("retry_count", 0),
                max_retries=step_dict.get("max_retries", 3),
            )
            steps.append(step)

        plan = WorkflowPlan(
            plan_id=plan_dict.get("plan_id", f"plan_{len(steps)}"),
            goal=plan_dict.get("goal", ""),
            steps=steps,
            reasoning=plan_dict.get("reasoning", ""),
            estimated_duration_minutes=plan_dict.get("estimated_duration_minutes", 5),
        )

        return plan
