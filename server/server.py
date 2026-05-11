"""
Main MCP Server for Power BI Agent.

Implements FastMCP server that exposes all PBIP tools as MCP resources
and tools. Run with: python server/server.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .metadata_tools import MetadataTools
from .dax_tools import DAXTools
from .visual_tools import VisualTools
from .git_tools import GitTools
from .validator import ValidatorTools

# Load environment variables
load_dotenv()

# Get PBIP root from environment or use current directory
PBIP_ROOT = Path(os.getenv("PBIP_ROOT", ".")).resolve()

# Initialize MCP server
mcp = FastMCP("power-bi-agent")

# Initialize tools
metadata_tools = MetadataTools(PBIP_ROOT)
dax_tools = DAXTools(PBIP_ROOT)
visual_tools = VisualTools(PBIP_ROOT)
git_tools = GitTools(PBIP_ROOT)
validator_tools = ValidatorTools(PBIP_ROOT)


# ============================================================================
# METADATA TOOLS
# ============================================================================


@mcp.tool()
def hello() -> dict:
    """Health check endpoint for MCP server."""
    return metadata_tools.hello()


@mcp.tool()
def list_pages() -> dict:
    """List all pages in the report."""
    return metadata_tools.list_pages()


@mcp.tool()
def list_visuals(page_id: str) -> dict:
    """List all visuals on a specific page."""
    return metadata_tools.list_visuals(page_id)


@mcp.tool()
def list_tables() -> dict:
    """List all tables in the semantic model."""
    return metadata_tools.list_tables()


@mcp.tool()
def list_measures(table_name: str = None) -> dict:
    """List all measures in the semantic model."""
    return metadata_tools.list_measures(table_name)


@mcp.tool()
def list_columns(table_name: str) -> dict:
    """List all columns in a specific table."""
    return metadata_tools.list_columns(table_name)


@mcp.tool()
def get_visual_details(page_id: str, visual_id: str) -> dict:
    """Get detailed information about a specific visual."""
    return metadata_tools.get_visual_details(page_id, visual_id)


@mcp.tool()
def get_table_details(table_name: str) -> dict:
    """Get detailed information about a specific table."""
    return metadata_tools.get_table_details(table_name)


@mcp.tool()
def get_measure_details(measure_name: str) -> dict:
    """Get detailed information about a specific measure."""
    return metadata_tools.get_measure_details(measure_name)


@mcp.tool()
def search_visuals(search_term: str) -> dict:
    """Search for visuals by name or title."""
    return metadata_tools.search_visuals(search_term)


@mcp.tool()
def search_measures(search_term: str) -> dict:
    """Search for measures by name or expression."""
    return metadata_tools.search_measures(search_term)


@mcp.tool()
def get_report_summary() -> dict:
    """Get high-level summary of the entire report."""
    return metadata_tools.get_report_summary()


# ============================================================================
# DAX TOOLS
# ============================================================================


@mcp.tool()
def create_measure(
    measure_name: str,
    expression: str,
    table_name: str,
    description: str = "",
    format_string: str = "",
    data_type: str = "double",
    display_folder: str = "",
    is_hidden: bool = False,
) -> dict:
    """Create a new measure in the semantic model."""
    return dax_tools.create_measure(
        measure_name=measure_name,
        expression=expression,
        table_name=table_name,
        description=description,
        format_string=format_string,
        data_type=data_type,
        display_folder=display_folder,
        is_hidden=is_hidden,
    )


@mcp.tool()
def update_measure(
    measure_name: str,
    expression: str = None,
    description: str = None,
    format_string: str = None,
    is_hidden: bool = None,
) -> dict:
    """Update an existing measure."""
    return dax_tools.update_measure(
        measure_name=measure_name,
        expression=expression,
        description=description,
        format_string=format_string,
        is_hidden=is_hidden,
    )


@mcp.tool()
def validate_dax(expression: str) -> dict:
    """Validate a DAX expression for syntax and common errors."""
    return dax_tools.validate_dax(expression)


@mcp.tool()
def get_common_dax_patterns() -> dict:
    """Get common DAX patterns and templates."""
    return dax_tools.get_common_dax_patterns()


@mcp.tool()
def extract_dax_functions(expression: str) -> dict:
    """Extract all DAX functions used in expression."""
    return dax_tools.extract_dax_functions(expression)


@mcp.tool()
def get_dax_dependencies(expression: str) -> dict:
    """Extract table and column references from DAX expression."""
    return dax_tools.get_dax_dependencies(expression)


# ============================================================================
# VISUAL TOOLS
# ============================================================================


@mcp.tool()
def add_kpi_card(
    page_id: str,
    title: str,
    measure_name: str,
    table_name: str,
    x: float = 0,
    y: float = 0,
    width: float = 250,
    height: float = 250,
    display_units: str = "Auto",
    color: str = "#0078D4",
) -> dict:
    """Add a KPI card visual to a page."""
    return visual_tools.add_kpi_card(
        page_id=page_id,
        title=title,
        measure_name=measure_name,
        table_name=table_name,
        x=x,
        y=y,
        width=width,
        height=height,
        display_units=display_units,
        color=color,
    )


@mcp.tool()
def update_visual_title(page_id: str, visual_id: str, new_title: str) -> dict:
    """Update the title of a visual."""
    return visual_tools.update_visual_title(page_id, visual_id, new_title)


@mcp.tool()
def move_visual(page_id: str, visual_id: str, x: float, y: float) -> dict:
    """Move a visual to a new position."""
    return visual_tools.move_visual(page_id, visual_id, x, y)


@mcp.tool()
def resize_visual(page_id: str, visual_id: str, width: float, height: float) -> dict:
    """Resize a visual."""
    return visual_tools.resize_visual(page_id, visual_id, width, height)


@mcp.tool()
def replace_visual(
    page_id: str,
    visual_id: str,
    new_visual_type: str,
    preserve_bindings: bool = True,
) -> dict:
    """Replace a visual with a different type."""
    return visual_tools.replace_visual(page_id, visual_id, new_visual_type, preserve_bindings)


@mcp.tool()
def duplicate_visual(page_id: str, visual_id: str, offset_x: float = 300) -> dict:
    """Duplicate a visual on the same page."""
    return visual_tools.duplicate_visual(page_id, visual_id, offset_x)


@mcp.tool()
def delete_visual(page_id: str, visual_id: str) -> dict:
    """Delete a visual from a page."""
    return visual_tools.delete_visual(page_id, visual_id)


@mcp.tool()
def batch_update_visuals(page_id: str, visual_updates: list) -> dict:
    """Update multiple visuals in batch."""
    return visual_tools.batch_update_visuals(page_id, visual_updates)


@mcp.tool()
def get_visual_layout_info(page_id: str) -> dict:
    """Get information about visual layout on a page."""
    return visual_tools.get_visual_layout_info(page_id)


@mcp.tool()
def auto_arrange_visuals(page_id: str, columns: int = 2, padding: float = 20) -> dict:
    """Auto-arrange visuals on a page in grid layout."""
    return visual_tools.auto_arrange_visuals(page_id, columns, padding)


# ============================================================================
# GIT TOOLS
# ============================================================================


@mcp.tool()
def git_commit(
    message: str,
    files: list = None,
    author: str = "Power BI Agent",
    email: str = "agent@powerbi.local",
) -> dict:
    """Create a git commit for PBIP changes."""
    return git_tools.git_commit(message, files, author, email)


@mcp.tool()
def get_status() -> dict:
    """Get current Git status."""
    return git_tools.get_status()


@mcp.tool()
def get_commit_history(max_commits: int = 10) -> dict:
    """Get recent commit history."""
    return git_tools.get_commit_history(max_commits)


@mcp.tool()
def create_branch(branch_name: str) -> dict:
    """Create a new branch."""
    return git_tools.create_branch(branch_name)


@mcp.tool()
def switch_branch(branch_name: str) -> dict:
    """Switch to a different branch."""
    return git_tools.switch_branch(branch_name)


@mcp.tool()
def list_branches() -> dict:
    """List all branches."""
    return git_tools.list_branches()


@mcp.tool()
def rollback_changes(files: list = None) -> dict:
    """Rollback uncommitted changes."""
    return git_tools.rollback_changes(files)


@mcp.tool()
def tag_release(tag_name: str, message: str = "") -> dict:
    """Create a release tag."""
    return git_tools.tag_release(tag_name, message)


@mcp.tool()
def get_diff(commit_hash: str = None) -> dict:
    """Get diff between commits or current and HEAD."""
    return git_tools.get_diff(commit_hash)


# ============================================================================
# VALIDATION TOOLS
# ============================================================================


@mcp.tool()
def validate_report() -> dict:
    """Validate entire report structure."""
    return validator_tools.validate_report()


@mcp.tool()
def validate_visual(page_id: str, visual_id: str) -> dict:
    """Validate a specific visual."""
    return validator_tools.validate_visual(page_id, visual_id)


@mcp.tool()
def validate_measure(measure_name: str) -> dict:
    """Validate a specific measure."""
    return validator_tools.validate_measure(measure_name)


@mcp.tool()
def validate_table(table_name: str) -> dict:
    """Validate a specific table."""
    return validator_tools.validate_table(table_name)


@mcp.tool()
def get_validation_summary() -> dict:
    """Get quick validation summary without detailed errors."""
    return validator_tools.get_validation_summary()


# ============================================================================
# SERVER LIFECYCLE
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    # Start FastMCP server
    print(f"Starting Power BI MCP Agent Server")
    print(f"PBIP Root: {PBIP_ROOT}")
    print(f"Listening on http://localhost:8000")
    print(f"Visit http://localhost:8000/docs for API documentation")

    uvicorn.run(
        "server.server:mcp",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
