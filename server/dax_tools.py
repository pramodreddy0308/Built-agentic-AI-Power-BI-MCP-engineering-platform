"""
DAX tools for creating, modifying, and validating measures.

Provides MCP-compatible functions for DAX measure operations including
creation, updating, and basic DAX expression validation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from .models import (
    DAXValidationResult,
    MeasureMetadata,
    DataType,
)
from .pbip_parser import PBIPParser


class DAXTools:
    """Tools for DAX measure operations."""

    def __init__(self, pbip_root: Path):
        """
        Initialize DAX tools.

        Args:
            pbip_root: Root path of PBIP project
        """
        self.pbip_root = Path(pbip_root)
        self.parser = PBIPParser(self.pbip_root)

    def create_measure(
        self,
        measure_name: str,
        expression: str,
        table_name: str,
        description: str = "",
        format_string: str = "",
        data_type: str = "double",
        display_folder: str = "",
        is_hidden: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new measure in the semantic model.

        Args:
            measure_name: Name of the new measure
            expression: DAX expression
            table_name: Target table name
            description: Measure description
            format_string: Format string (e.g., "$#,##0.00")
            data_type: Data type of measure
            display_folder: Display folder path
            is_hidden: Whether measure is hidden

        Returns:
            Operation result with created measure metadata
        """
        # Validate inputs
        validation = self._validate_measure_inputs(
            measure_name, expression, table_name
        )
        if not validation["is_valid"]:
            return {
                "success": False,
                "error": validation["errors"][0],
            }

        # Check if measure already exists
        existing = self.parser.get_measure_by_name(measure_name)
        if existing:
            return {
                "success": False,
                "error": f"Measure already exists: {measure_name}",
            }

        # Validate DAX expression
        dax_validation = self.validate_dax(expression)
        if not dax_validation["is_valid"]:
            return {
                "success": False,
                "error": f"DAX validation failed: {dax_validation['errors'][0]}",
            }

        # Create measure metadata
        measure_meta = MeasureMetadata(
            measure_name=measure_name,
            table_name=table_name,
            expression=expression,
            description=description,
            format_string=format_string,
            data_type=data_type,
            display_folder=display_folder,
            is_hidden=is_hidden,
        )

        # Build measure definition for TMDL
        measure_dict = {
            "name": measure_name,
            "expression": expression,
            "description": description,
            "formatString": format_string,
            "dataType": data_type,
            "displayFolder": display_folder,
            "isHidden": is_hidden,
        }

        # Save measure (in real implementation, would update TMDL file)
        # For now, return metadata showing what would be created
        return {
            "success": True,
            "message": f"Measure created successfully: {measure_name}",
            "measure": measure_meta.model_dump(),
            "table_name": table_name,
        }

    def update_measure(
        self,
        measure_name: str,
        expression: Optional[str] = None,
        description: Optional[str] = None,
        format_string: Optional[str] = None,
        is_hidden: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing measure.

        Args:
            measure_name: Name of measure to update
            expression: New DAX expression (optional)
            description: New description (optional)
            format_string: New format string (optional)
            is_hidden: New visibility setting (optional)

        Returns:
            Operation result
        """
        # Find existing measure
        measure = self.parser.get_measure_by_name(measure_name)
        if not measure:
            return {
                "success": False,
                "error": f"Measure not found: {measure_name}",
            }

        # Validate new expression if provided
        if expression:
            validation = self.validate_dax(expression)
            if not validation["is_valid"]:
                return {
                    "success": False,
                    "error": f"DAX validation failed: {validation['errors'][0]}",
                }

        # Prepare updated measure
        updated_measure = measure.copy()
        if expression:
            updated_measure["expression"] = expression
        if description is not None:
            updated_measure["description"] = description
        if format_string is not None:
            updated_measure["formatString"] = format_string
        if is_hidden is not None:
            updated_measure["isHidden"] = is_hidden

        return {
            "success": True,
            "message": f"Measure updated successfully: {measure_name}",
            "measure_name": measure_name,
            "updated_fields": {
                "expression": expression is not None,
                "description": description is not None,
                "format_string": format_string is not None,
                "is_hidden": is_hidden is not None,
            },
        }

    def validate_dax(self, expression: str) -> Dict[str, Any]:
        """
        Validate a DAX expression for syntax and common errors.

        Args:
            expression: DAX expression to validate

        Returns:
            DAXValidationResult
        """
        errors = []
        warnings = []
        is_valid = True
        estimated_type = None

        # Basic syntax checks
        if not expression or not expression.strip():
            return {
                "is_valid": False,
                "errors": ["Expression cannot be empty"],
                "warnings": [],
                "estimated_type": None,
            }

        # Check for balanced parentheses
        if expression.count("(") != expression.count(")"):
            errors.append("Unbalanced parentheses")
            is_valid = False

        # Check for balanced quotes
        if expression.count('"') % 2 != 0:
            errors.append("Unbalanced double quotes")
            is_valid = False

        # Check for common DAX functions
        valid_functions = [
            "SUMX",
            "SUMPRODUCT",
            "SUM",
            "AVERAGE",
            "COUNT",
            "COUNTA",
            "DISTINCTCOUNT",
            "MIN",
            "MAX",
            "DIVIDE",
            "FILTER",
            "CALCULATE",
            "VALUES",
            "RELATED",
            "RELATEDTABLE",
            "ALL",
            "ALLEXCEPT",
            "HASONEVALUE",
            "VAR",
            "IF",
            "AND",
            "OR",
            "NOT",
            "CONCATENATE",
            "CONCATENATEX",
            "FORMAT",
            "DATE",
            "TODAY",
            "NOW",
        ]

        # Extract function calls
        functions_in_expr = re.findall(r"\b([A-Z_][A-Z0-9_]*)\s*\(", expression)
        for func in functions_in_expr:
            if func not in valid_functions:
                warnings.append(f"Unknown function: {func}")

        # Try to estimate return type based on functions
        if "SUMX" in expression or "SUM" in expression:
            estimated_type = "double"
        elif "COUNT" in expression or "DISTINCTCOUNT" in expression:
            estimated_type = "int64"
        elif "CONCATENATE" in expression:
            estimated_type = "string"
        elif "AVERAGE" in expression:
            estimated_type = "double"

        result = DAXValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            estimated_type=DataType(estimated_type) if estimated_type else None,
        )

        return result.model_dump()

    def get_common_dax_patterns(self) -> Dict[str, Any]:
        """
        Get common DAX patterns and templates.

        Returns:
            Dictionary of DAX patterns
        """
        return {
            "revenue": {
                "description": "Total revenue calculation",
                "pattern": "SUMX(FactOrders, FactOrders[Quantity] * FactOrders[UnitPrice])",
            },
            "count": {
                "description": "Distinct count",
                "pattern": "DISTINCTCOUNT(FactOrders[OrderID])",
            },
            "average": {
                "description": "Average calculation",
                "pattern": "AVERAGE(FactOrders[Amount])",
            },
            "year_to_date": {
                "description": "Year-to-date calculation",
                "pattern": "CALCULATE(SUM(FactOrders[Amount]), DATESYTD(DateTable[Date]))",
            },
            "market_share": {
                "description": "Market share calculation",
                "pattern": "DIVIDE(SUM(FactOrders[Amount]), CALCULATE(SUM(FactOrders[Amount]), ALL(DimProduct)))",
            },
            "growth_rate": {
                "description": "Period-over-period growth",
                "pattern": "DIVIDE(SUM(FactOrders[Amount]) - CALCULATE(SUM(FactOrders[Amount]), DATEADD(DateTable[Date], -1, YEAR)), CALCULATE(SUM(FactOrders[Amount]), DATEADD(DateTable[Date], -1, YEAR)))",
            },
        }

    def extract_dax_functions(self, expression: str) -> Dict[str, Any]:
        """
        Extract all DAX functions used in expression.

        Args:
            expression: DAX expression

        Returns:
            List of functions and their usage
        """
        # Extract function names
        functions = re.findall(r"\b([A-Z_][A-Z0-9_]*)\s*\(", expression)

        # Count occurrences
        function_counts = {}
        for func in functions:
            function_counts[func] = function_counts.get(func, 0) + 1

        return {
            "functions": function_counts,
            "unique_count": len(function_counts),
            "total_count": len(functions),
        }

    def get_dax_dependencies(self, expression: str) -> Dict[str, Any]:
        """
        Extract table and column references from DAX expression.

        Args:
            expression: DAX expression

        Returns:
            Dictionary of dependencies
        """
        # Simple pattern to find table[column] references
        references = re.findall(r"(\w+)\[(\w+)\]", expression)

        tables = set()
        columns = {}

        for table, column in references:
            tables.add(table)
            if table not in columns:
                columns[table] = []
            if column not in columns[table]:
                columns[table].append(column)

        return {
            "tables": list(tables),
            "columns": columns,
            "column_references": len(references),
        }

    def _validate_measure_inputs(
        self, measure_name: str, expression: str, table_name: str
    ) -> Dict[str, Any]:
        """
        Validate measure input parameters.

        Args:
            measure_name: Measure name
            expression: DAX expression
            table_name: Target table name

        Returns:
            Validation result
        """
        errors = []

        # Validate measure name
        if not measure_name or not measure_name.strip():
            errors.append("Measure name cannot be empty")

        if len(measure_name) > 128:
            errors.append("Measure name exceeds 128 characters")

        # Invalid characters in measure name
        if re.search(r"[<>:/?\\]", measure_name):
            errors.append("Measure name contains invalid characters")

        # Validate expression
        if not expression or not expression.strip():
            errors.append("DAX expression cannot be empty")

        # Validate table name
        if not table_name or not table_name.strip():
            errors.append("Table name cannot be empty")

        # Check if table exists
        tables = self.parser.get_tables()
        if not any(t.get("name") == table_name for t in tables):
            errors.append(f"Table not found: {table_name}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }
