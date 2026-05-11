"""
Tool router for MCP tool execution.

Routes workflow steps to appropriate MCP tools and manages parameter
preparation, result processing, and error handling.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from .prompts import TOOL_ROUTER_PROMPT


class ToolRouter:
    """Routes workflow steps to MCP tools."""

    def __init__(self, mcp_client):
        """
        Initialize tool router.

        Args:
            mcp_client: MCP client for tool execution
        """
        self.mcp_client = mcp_client
        self.tool_catalog = self._build_tool_catalog()

    def _build_tool_catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        Build catalog of available MCP tools.

        Returns:
            Dictionary mapping tool names to their specifications
        """
        return {
            # Metadata tools
            "hello": {
                "category": "inspection",
                "params": [],
            },
            "list_pages": {
                "category": "inspection",
                "params": [],
            },
            "list_visuals": {
                "category": "inspection",
                "params": ["page_id"],
            },
            "list_tables": {
                "category": "inspection",
                "params": [],
            },
            "list_measures": {
                "category": "inspection",
                "params": ["table_name?"],
            },
            "list_columns": {
                "category": "inspection",
                "params": ["table_name"],
            },
            "get_visual_details": {
                "category": "inspection",
                "params": ["page_id", "visual_id"],
            },
            "get_table_details": {
                "category": "inspection",
                "params": ["table_name"],
            },
            "get_measure_details": {
                "category": "inspection",
                "params": ["measure_name"],
            },
            "search_visuals": {
                "category": "inspection",
                "params": ["search_term"],
            },
            "search_measures": {
                "category": "inspection",
                "params": ["search_term"],
            },
            "get_report_summary": {
                "category": "inspection",
                "params": [],
            },
            # DAX tools
            "create_measure": {
                "category": "creation",
                "params": ["measure_name", "expression", "table_name", "description?", "format_string?"],
            },
            "update_measure": {
                "category": "modification",
                "params": ["measure_name", "expression?", "description?", "format_string?"],
            },
            "validate_dax": {
                "category": "validation",
                "params": ["expression"],
            },
            "get_common_dax_patterns": {
                "category": "inspection",
                "params": [],
            },
            "extract_dax_functions": {
                "category": "inspection",
                "params": ["expression"],
            },
            # Visual tools
            "add_kpi_card": {
                "category": "creation",
                "params": ["page_id", "title", "measure_name", "table_name", "x?", "y?"],
            },
            "update_visual_title": {
                "category": "modification",
                "params": ["page_id", "visual_id", "new_title"],
            },
            "move_visual": {
                "category": "modification",
                "params": ["page_id", "visual_id", "x", "y"],
            },
            "resize_visual": {
                "category": "modification",
                "params": ["page_id", "visual_id", "width", "height"],
            },
            "replace_visual": {
                "category": "modification",
                "params": ["page_id", "visual_id", "new_visual_type", "preserve_bindings?"],
            },
            "delete_visual": {
                "category": "deletion",
                "params": ["page_id", "visual_id"],
            },
            # Git tools
            "git_commit": {
                "category": "version_control",
                "params": ["message", "files?", "author?"],
            },
            "get_status": {
                "category": "inspection",
                "params": [],
            },
            "rollback_changes": {
                "category": "modification",
                "params": ["files?"],
            },
            # Validation tools
            "validate_report": {
                "category": "validation",
                "params": [],
            },
            "validate_visual": {
                "category": "validation",
                "params": ["page_id", "visual_id"],
            },
            "validate_measure": {
                "category": "validation",
                "params": ["measure_name"],
            },
            "validate_table": {
                "category": "validation",
                "params": ["table_name"],
            },
        }

    def route_step(
        self,
        step: Dict[str, Any],
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Route a workflow step to the appropriate MCP tool.

        Args:
            step: Workflow step specification
            previous_results: Results from previous steps

        Returns:
            Tool execution result
        """
        tool_name = step.get("tool_name")
        tool_params = step.get("tool_params", {})

        # Validate tool exists
        if tool_name not in self.tool_catalog:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "step_id": step.get("step_id"),
            }

        # Prepare parameters
        prepared_params = self._prepare_parameters(
            tool_name, tool_params, previous_results
        )

        if "error" in prepared_params:
            return {
                "success": False,
                "error": prepared_params["error"],
                "step_id": step.get("step_id"),
            }

        # Call MCP tool
        result = self._execute_tool(tool_name, prepared_params)

        # Process result
        processed = self._process_result(tool_name, result)

        return {
            "success": processed.get("success", True),
            "tool_name": tool_name,
            "step_id": step.get("step_id"),
            "data": processed,
            "timestamp": datetime.now().isoformat(),
        }

    def _prepare_parameters(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare parameters for tool execution.

        Args:
            tool_name: Name of tool
            tool_params: Raw parameters from step
            previous_results: Results from previous steps

        Returns:
            Prepared parameters or error
        """
        prepared = {}

        # Get tool specification
        tool_spec = self.tool_catalog.get(tool_name, {})
        required_params = [p for p in tool_spec.get("params", []) if not p.endswith("?")]

        for param_name in tool_spec.get("params", []):
            # Remove optional marker
            clean_name = param_name.rstrip("?")
            is_optional = param_name.endswith("?")

            # Check if in tool_params
            if clean_name in tool_params:
                prepared[clean_name] = tool_params[clean_name]
            # Check if in previous results (parameter substitution)
            elif clean_name in previous_results:
                prepared[clean_name] = previous_results[clean_name]
            # Check if required
            elif not is_optional:
                return {
                    "error": f"Missing required parameter: {clean_name}",
                }

        return prepared

    def _execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute MCP tool with parameters.

        Args:
            tool_name: Tool to execute
            params: Tool parameters

        Returns:
            Tool result
        """
        try:
            # In real implementation, would call actual MCP client
            # For now, return mock result
            result = {
                "success": True,
                "tool_name": tool_name,
                "data": {
                    "message": f"Tool {tool_name} executed successfully",
                },
            }
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
            }

    def _process_result(
        self,
        tool_name: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process tool result for downstream consumption.

        Args:
            tool_name: Tool name
            result: Raw tool result

        Returns:
            Processed result
        """
        # Extract key data based on tool type
        if tool_name == "list_pages":
            return {
                "success": result.get("success", True),
                "pages": result.get("data", {}).get("pages", []),
                "page_count": result.get("data", {}).get("count", 0),
            }

        elif tool_name == "list_visuals":
            return {
                "success": result.get("success", True),
                "visuals": result.get("data", {}).get("visuals", []),
                "visual_count": result.get("data", {}).get("count", 0),
            }

        elif tool_name == "get_measure_details":
            data = result.get("data", {})
            if data.get("success") is False:
                return {"success": False, "error": data.get("error")}
            return {
                "success": True,
                "measure_exists": True,
                "measure_name": data.get("measure_name"),
                "expression": data.get("expression"),
            }

        elif tool_name == "create_measure":
            data = result.get("data", {})
            return {
                "success": data.get("success", False),
                "message": data.get("message", ""),
                "measure_name": data.get("measure_name"),
            }

        elif tool_name == "validate_report":
            data = result.get("data", {})
            return {
                "success": data.get("is_valid", False),
                "errors": data.get("errors", []),
                "warnings": data.get("warnings", []),
            }

        else:
            # Default processing
            return result.get("data", result)

    def validate_step_feasibility(
        self,
        step: Dict[str, Any],
        tool_catalog: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate that a step can be executed.

        Args:
            step: Workflow step
            tool_catalog: Available tools

        Returns:
            Feasibility report
        """
        tool_name = step.get("tool_name")
        issues = []

        # Check tool exists
        if tool_name not in self.tool_catalog:
            issues.append(f"Tool not found: {tool_name}")

        # Check tool parameters
        tool_spec = self.tool_catalog.get(tool_name, {})
        tool_params = step.get("tool_params", {})
        required_params = [p for p in tool_spec.get("params", []) if not p.endswith("?")]

        for required in required_params:
            if required not in tool_params:
                issues.append(f"Missing required parameter: {required}")

        return {
            "is_feasible": len(issues) == 0,
            "issues": issues,
            "tool_name": tool_name,
        }

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool.

        Args:
            tool_name: Tool name

        Returns:
            Tool information
        """
        spec = self.tool_catalog.get(tool_name)

        if not spec:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
            }

        return {
            "success": True,
            "tool_name": tool_name,
            "category": spec.get("category"),
            "parameters": spec.get("params", []),
        }

    def list_tools_by_category(self, category: str) -> Dict[str, Any]:
        """
        List all tools in a specific category.

        Args:
            category: Tool category

        Returns:
            Tools in category
        """
        tools = [
            name
            for name, spec in self.tool_catalog.items()
            if spec.get("category") == category
        ]

        return {
            "category": category,
            "tools": tools,
            "count": len(tools),
        }
