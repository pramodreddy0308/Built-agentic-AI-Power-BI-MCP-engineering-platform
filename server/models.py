"""
Data models for Power BI MCP Agent.

Provides structured data classes and Pydantic models for PBIP components,
measures, visuals, pages, and MCP tool operations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================


class VisualType(str, Enum):
    """Supported Power BI visual types."""
    CARD = "card"
    KPI = "kpi"
    GAUGE = "gauge"
    LINE_CHART = "lineChart"
    COLUMN_CHART = "columnChart"
    BAR_CHART = "barChart"
    PIE_CHART = "pieChart"
    CLUSTERED_BAR = "clusteredBar"
    CLUSTERED_COLUMN = "clusteredColumn"
    TABLE = "table"
    MATRIX = "matrix"
    SLICER = "slicer"
    UNKNOWN = "unknown"


class DataType(str, Enum):
    """DAX data types."""
    INTEGER = "int64"
    DECIMAL = "double"
    TEXT = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    CURRENCY = "currency"


class MeasureAggregation(str, Enum):
    """Measure aggregation functions."""
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    COUNT = "COUNT"
    DISTINCTCOUNT = "DISTINCTCOUNT"
    MIN = "MIN"
    MAX = "MAX"
    DIVIDE = "DIVIDE"


# ============================================================================
# PYDANTIC MODELS FOR API RESPONSES
# ============================================================================


class PageMetadata(BaseModel):
    """Metadata for a report page."""
    page_id: str = Field(..., description="Unique page identifier")
    page_name: str = Field(..., description="Display name of page")
    display_name: str = Field(..., description="User-friendly page name")
    ordinal: int = Field(..., description="Page order in report")
    visibility: bool = Field(default=True, description="Whether page is visible")

    class Config:
        json_schema_extra = {
            "example": {
                "page_id": "e9d880b5977088da6d5a",
                "page_name": "Page1",
                "display_name": "Executive Dashboard",
                "ordinal": 0,
                "visibility": True,
            }
        }


class VisualMetadata(BaseModel):
    """Metadata for a report visual."""
    visual_id: str = Field(..., description="Unique visual identifier")
    visual_name: str = Field(..., description="Display name")
    visual_type: VisualType = Field(..., description="Type of visual")
    page_id: str = Field(..., description="Parent page ID")
    title: str = Field(default="", description="Visual title")
    x: float = Field(default=0, description="X position")
    y: float = Field(default=0, description="Y position")
    width: float = Field(default=0, description="Width")
    height: float = Field(default=0, description="Height")
    bindings: Dict[str, Any] = Field(default_factory=dict, description="Data bindings")

    class Config:
        json_schema_extra = {
            "example": {
                "visual_id": "9b04c5f13045851cae59",
                "visual_name": "Visual1",
                "visual_type": "kpi",
                "page_id": "e9d880b5977088da6d5a",
                "title": "Total Revenue",
                "x": 0,
                "y": 0,
                "width": 250,
                "height": 250,
            }
        }


class TableMetadata(BaseModel):
    """Metadata for a semantic model table."""
    table_name: str = Field(..., description="Table name")
    table_display_name: str = Field(..., description="Display name")
    is_hidden: bool = Field(default=False, description="Whether table is hidden")
    is_private: bool = Field(default=False, description="Whether table is private")
    description: str = Field(default="", description="Table description")

    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "FactOrders",
                "table_display_name": "Orders",
                "is_hidden": False,
                "is_private": False,
                "description": "Order transactions",
            }
        }


class ColumnMetadata(BaseModel):
    """Metadata for a semantic model column."""
    column_name: str = Field(..., description="Column name")
    table_name: str = Field(..., description="Parent table name")
    data_type: DataType = Field(..., description="Column data type")
    is_key: bool = Field(default=False, description="Whether column is a key")
    description: str = Field(default="", description="Column description")

    class Config:
        json_schema_extra = {
            "example": {
                "column_name": "OrderID",
                "table_name": "FactOrders",
                "data_type": "int64",
                "is_key": True,
                "description": "Order identifier",
            }
        }


class MeasureMetadata(BaseModel):
    """Metadata for a DAX measure."""
    measure_name: str = Field(..., description="Measure name")
    table_name: str = Field(..., description="Parent table name")
    expression: str = Field(..., description="DAX expression")
    data_type: DataType = Field(default=DataType.DECIMAL, description="Measure data type")
    format_string: str = Field(default="", description="Format string (e.g., '0.00%')")
    description: str = Field(default="", description="Measure description")
    display_folder: str = Field(default="", description="Display folder path")
    is_hidden: bool = Field(default=False, description="Whether measure is hidden")

    class Config:
        json_schema_extra = {
            "example": {
                "measure_name": "Total Revenue",
                "table_name": "FactOrders",
                "expression": "SUMX(FactOrders, FactOrders[Quantity] * FactOrders[UnitPrice])",
                "data_type": "currency",
                "format_string": "$#,##0.00",
                "description": "Total revenue from orders",
                "display_folder": "Financial",
                "is_hidden": False,
            }
        }


class DAXValidationResult(BaseModel):
    """Result of DAX expression validation."""
    is_valid: bool = Field(..., description="Whether DAX is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    estimated_type: Optional[DataType] = Field(None, description="Estimated return type")

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "estimated_type": "currency",
            }
        }


class ReportValidationResult(BaseModel):
    """Result of full report validation."""
    is_valid: bool = Field(..., description="Whether report is valid")
    errors: List[str] = Field(default_factory=list, description="Critical errors")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    pages_count: int = Field(..., description="Number of pages")
    visuals_count: int = Field(..., description="Number of visuals")
    measures_count: int = Field(..., description="Number of measures")

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "pages_count": 2,
                "visuals_count": 15,
                "measures_count": 8,
            }
        }


class ToolExecutionResult(BaseModel):
    """Result of MCP tool execution."""
    success: bool = Field(..., description="Whether tool executed successfully")
    tool_name: str = Field(..., description="Name of executed tool")
    message: str = Field(..., description="Execution message")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Execution timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "tool_name": "create_measure",
                "message": "Measure created successfully",
                "data": {"measure_name": "Total Revenue"},
                "error": None,
                "timestamp": "2024-05-10T10:30:00",
            }
        }


class WorkflowStep(BaseModel):
    """Single step in a workflow."""
    step_id: str = Field(..., description="Unique step identifier")
    step_name: str = Field(..., description="Human-readable step name")
    tool_name: str = Field(..., description="MCP tool to call")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    depends_on: List[str] = Field(default_factory=list, description="Dependency step IDs")
    retry_count: int = Field(default=0, description="Number of retries")
    max_retries: int = Field(default=3, description="Maximum retries allowed")

    class Config:
        json_schema_extra = {
            "example": {
                "step_id": "step_1",
                "step_name": "Create Gross Margin measure",
                "tool_name": "create_measure",
                "tool_params": {"measure_name": "Gross Margin", "expression": "..."},
                "depends_on": [],
                "retry_count": 0,
                "max_retries": 3,
            }
        }


class WorkflowPlan(BaseModel):
    """Complete workflow plan from planner agent."""
    plan_id: str = Field(..., description="Unique plan identifier")
    goal: str = Field(..., description="Workflow goal/objective")
    steps: List[WorkflowStep] = Field(..., description="Ordered workflow steps")
    reasoning: str = Field(..., description="Agent's reasoning for plan")
    estimated_duration_minutes: float = Field(default=5, description="Estimated duration")

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_001",
                "goal": "Add Gross Margin KPI card to Executive Dashboard",
                "steps": [
                    {
                        "step_id": "step_1",
                        "step_name": "Check if Gross Margin measure exists",
                        "tool_name": "list_measures",
                        "tool_params": {},
                    }
                ],
                "reasoning": "First check measures, then add KPI...",
                "estimated_duration_minutes": 5,
            }
        }


class KPICardConfig(BaseModel):
    """Configuration for KPI card visual."""
    title: str = Field(..., description="KPI title")
    measure_name: str = Field(..., description="Measure to display")
    table_name: str = Field(..., description="Measure's table")
    display_units: str = Field(default="Auto", description="Display units (Auto, Thousands, Millions, Billions)")
    color: str = Field(default="#0078D4", description="Card color")
    x: float = Field(default=0, description="X position")
    y: float = Field(default=0, description="Y position")
    width: float = Field(default=250, description="Width")
    height: float = Field(default=250, description="Height")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Total Revenue",
                "measure_name": "Total Revenue",
                "table_name": "FactOrders",
                "display_units": "Millions",
                "color": "#0078D4",
                "x": 0,
                "y": 0,
                "width": 250,
                "height": 250,
            }
        }


# ============================================================================
# DATACLASSES FOR INTERNAL USE
# ============================================================================


@dataclass
class PBIPStructure:
    """Structure representing a PBIP project."""
    project_root: Path
    report_folder: Path
    semantic_model_folder: Path
    pbip_file: Path
    report_definition: Optional[Dict[str, Any]] = None
    semantic_model_definition: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GitCommitInfo:
    """Information about a git commit."""
    commit_hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WorkflowExecutionState:
    """State tracking for workflow execution."""
    workflow_id: str
    current_step_id: str
    steps_completed: int
    total_steps: int
    status: str  # pending, running, completed, failed
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)
    step_results: Dict[str, ToolExecutionResult] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        data["step_results"] = {
            k: v.model_dump() for k, v in self.step_results.items()
        }
        return data
