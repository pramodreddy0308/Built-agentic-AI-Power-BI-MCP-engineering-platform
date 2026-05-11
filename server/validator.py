"""
Validation tools for report and component validation.

Provides MCP-compatible functions for validating report structure,
measures, visuals, and overall semantic integrity.
"""

from pathlib import Path
from typing import Any, Dict, List

from .models import ReportValidationResult
from .pbip_parser import PBIPParser


class ValidatorTools:
    """Tools for PBIP validation."""

    def __init__(self, pbip_root: Path):
        """
        Initialize validator tools.

        Args:
            pbip_root: Root path of PBIP project
        """
        self.pbip_root = Path(pbip_root)
        self.parser = PBIPParser(self.pbip_root)

    def validate_report(self) -> Dict[str, Any]:
        """
        Validate entire report structure.

        Returns:
            Comprehensive validation result
        """
        errors = []
        warnings = []

        # Validate pages
        pages_result = self._validate_pages()
        errors.extend(pages_result["errors"])
        warnings.extend(pages_result["warnings"])

        # Validate visuals
        visuals_result = self._validate_visuals()
        errors.extend(visuals_result["errors"])
        warnings.extend(visuals_result["warnings"])

        # Validate semantic model
        model_result = self._validate_semantic_model()
        errors.extend(model_result["errors"])
        warnings.extend(model_result["warnings"])

        # Validate relationships
        relationships_result = self._validate_relationships()
        errors.extend(relationships_result["errors"])
        warnings.extend(relationships_result["warnings"])

        # Count components
        pages = self.parser.get_pages()
        tables = self.parser.get_tables()
        measures = self.parser.get_measures()

        total_visuals = 0
        for page in pages:
            page_id = page.get("name", "")
            visuals = self.parser.get_visuals(page_id)
            total_visuals += len(visuals)

        is_valid = len(errors) == 0

        result = ReportValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            pages_count=len(pages),
            visuals_count=total_visuals,
            measures_count=len(measures),
        )

        return result.model_dump()

    def validate_visual(self, page_id: str, visual_id: str) -> Dict[str, Any]:
        """
        Validate a specific visual.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier

        Returns:
            Visual validation result
        """
        errors = []
        warnings = []

        # Get visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Check visual properties
        if not visual.get("name"):
            warnings.append("Visual has no name")

        if not visual.get("title"):
            warnings.append("Visual has no title")

        # Check bindings
        bindings = visual.get("bindings", {})
        if not bindings:
            warnings.append("Visual has no data bindings")
        else:
            # Validate bindings reference valid tables/measures
            for binding_name, binding_config in bindings.items():
                if isinstance(binding_config, dict):
                    table = binding_config.get("table")
                    column = binding_config.get("column")

                    if table and column:
                        # Check if table exists
                        tables = self.parser.get_tables()
                        if not any(t.get("name") == table for t in tables):
                            errors.append(f"Binding references non-existent table: {table}")

        # Check position and size
        x = visual.get("x", 0)
        y = visual.get("y", 0)
        width = visual.get("width", 0)
        height = visual.get("height", 0)

        if width <= 0 or height <= 0:
            errors.append("Visual has invalid size")

        return {
            "success": len(errors) == 0,
            "visual_id": visual_id,
            "page_id": page_id,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_measure(self, measure_name: str) -> Dict[str, Any]:
        """
        Validate a specific measure.

        Args:
            measure_name: Name of measure

        Returns:
            Measure validation result
        """
        errors = []
        warnings = []

        # Get measure
        measure = self.parser.get_measure_by_name(measure_name)
        if not measure:
            return {
                "success": False,
                "error": f"Measure not found: {measure_name}",
            }

        expression = measure.get("expression", "")

        # Validate expression is not empty
        if not expression or not expression.strip():
            errors.append("Measure expression is empty")

        # Check for common issues
        if "SUM" in expression and "DISTINCT" not in expression:
            # SUM might accumulate inappropriately
            warnings.append("Measure uses SUM without DISTINCT consideration")

        if "CALCULATE" not in expression and "FILTER" not in expression:
            # Most complex measures need CALCULATE
            if expression.count("(") > 2:
                warnings.append("Complex expression without CALCULATE")

        # Check format string validity if present
        format_string = measure.get("formatString", "")
        if format_string:
            if not self._validate_format_string(format_string):
                errors.append(f"Invalid format string: {format_string}")

        return {
            "success": len(errors) == 0,
            "measure_name": measure_name,
            "table_name": measure.get("table_name", ""),
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def validate_table(self, table_name: str) -> Dict[str, Any]:
        """
        Validate a specific table.

        Args:
            table_name: Name of table

        Returns:
            Table validation result
        """
        errors = []
        warnings = []

        tables = self.parser.get_tables()
        table = next((t for t in tables if t.get("name") == table_name), None)

        if not table:
            return {
                "success": False,
                "error": f"Table not found: {table_name}",
            }

        # Get columns and measures
        columns = self.parser.get_columns(table_name)
        measures = self.parser.get_measures(table_name)

        # Check if table has data
        if not columns:
            warnings.append("Table has no columns")

        # Check for duplicate column names
        column_names = [c.get("name") for c in columns]
        duplicates = [name for name in column_names if column_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate column names: {duplicates}")

        # Check for naming conflicts between columns and measures
        measure_names = [m.get("name") for m in measures]
        conflicts = [name for name in column_names if name in measure_names]
        if conflicts:
            errors.append(f"Column/measure name conflicts: {conflicts}")

        return {
            "success": len(errors) == 0,
            "table_name": table_name,
            "column_count": len(columns),
            "measure_count": len(measures),
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_pages(self) -> Dict[str, List[str]]:
        """Validate all pages in report."""
        errors = []
        warnings = []

        pages = self.parser.get_pages()

        if not pages:
            errors.append("Report has no pages")
            return {"errors": errors, "warnings": warnings}

        for page in pages:
            page_id = page.get("name", "")
            if not page_id:
                errors.append("Page missing name")
                continue

            # Check if page folder exists
            page_folder = (
                self.pbip_root
                / f"{self.pbip_root.name}.Report"
                / "definition"
                / "pages"
                / page_id
            )
            if not page_folder.exists():
                errors.append(f"Page folder missing for: {page_id}")

        return {"errors": errors, "warnings": warnings}

    def _validate_visuals(self) -> Dict[str, List[str]]:
        """Validate all visuals in report."""
        errors = []
        warnings = []

        pages = self.parser.get_pages()

        for page in pages:
            page_id = page.get("name", "")
            visuals = self.parser.get_visuals(page_id)

            if not visuals:
                warnings.append(f"Page has no visuals: {page_id}")
                continue

            for visual in visuals:
                visual_id = visual.get("visual_id", "")

                # Check visual has required properties
                if not visual.get("name"):
                    warnings.append(f"Visual missing name on page {page_id}")

                # Validate visual type
                visual_type = visual.get("visualType", "unknown")
                if visual_type == "unknown":
                    warnings.append(f"Unknown visual type for {visual_id}")

        return {"errors": errors, "warnings": warnings}

    def _validate_semantic_model(self) -> Dict[str, List[str]]:
        """Validate semantic model structure."""
        errors = []
        warnings = []

        tables = self.parser.get_tables()

        if not tables:
            errors.append("Semantic model has no tables")
            return {"errors": errors, "warnings": warnings}

        for table in tables:
            table_name = table.get("name", "")
            if not table_name:
                errors.append("Table missing name")
                continue

            # Validate table has columns
            columns = self.parser.get_columns(table_name)
            if not columns:
                warnings.append(f"Table has no columns: {table_name}")

        return {"errors": errors, "warnings": warnings}

    def _validate_relationships(self) -> Dict[str, List[str]]:
        """Validate relationships in semantic model."""
        errors = []
        warnings = []

        # For now, basic validation - would need relationships definition
        # in real implementation

        return {"errors": errors, "warnings": warnings}

    def _validate_format_string(self, format_string: str) -> bool:
        """
        Validate Power BI format string syntax.

        Args:
            format_string: Format string to validate

        Returns:
            True if valid
        """
        if not format_string:
            return True

        # Valid Power BI format strings start with certain prefixes
        valid_prefixes = [
            "0",  # Numbers
            "#",  # Numbers with thousands separator
            "0.00",  # Decimal places
            "$",  # Currency
            "%",  # Percentage
            "d",  # Date
            "m/d/yyyy",  # Date format
        ]

        # Very basic validation - in production would be more comprehensive
        return any(format_string.startswith(p) for p in valid_prefixes) or len(format_string) <= 20

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get quick validation summary without detailed errors.

        Returns:
            Summary of validation status
        """
        pages = self.parser.get_pages()
        tables = self.parser.get_tables()
        measures = self.parser.get_measures()

        total_visuals = sum(
            len(self.parser.get_visuals(p.get("name", ""))) for p in pages
        )

        has_critical_issues = (
            len(pages) == 0 or len(tables) == 0
        )

        return {
            "health_status": "critical" if has_critical_issues else "healthy",
            "pages_count": len(pages),
            "tables_count": len(tables),
            "measures_count": len(measures),
            "visuals_count": total_visuals,
            "total_components": len(pages) + len(tables) + len(measures) + total_visuals,
        }
