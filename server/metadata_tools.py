"""
Metadata tools for inspecting Power BI project structure.

Provides MCP-compatible functions for reading pages, visuals, measures, tables,
and other report/model metadata.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import PageMetadata, VisualMetadata, TableMetadata, ColumnMetadata, MeasureMetadata, VisualType
from .pbip_parser import PBIPParser


class MetadataTools:
    """Tools for inspecting PBIP metadata."""

    def __init__(self, pbip_root: Path):
        """
        Initialize metadata tools.

        Args:
            pbip_root: Root path of PBIP project
        """
        self.pbip_root = Path(pbip_root)
        self.parser = PBIPParser(self.pbip_root)

    def hello(self) -> Dict[str, Any]:
        """
        Health check endpoint for MCP server.

        Returns:
            Status message
        """
        return {
            "status": "online",
            "message": "Power BI MCP Agent is ready",
            "pbip_root": str(self.pbip_root),
        }

    def list_pages(self) -> Dict[str, Any]:
        """
        List all pages in the report.

        Returns:
            Dictionary containing list of pages and page count
        """
        pages = self.parser.get_pages()

        # Convert to PageMetadata format
        pages_metadata = []
        for idx, page in enumerate(pages):
            try:
                page_meta = PageMetadata(
                    page_id=page.get("name", f"page_{idx}"),
                    page_name=page.get("name", f"Page {idx + 1}"),
                    display_name=page.get("displayName", page.get("name", f"Page {idx + 1}")),
                    ordinal=idx,
                    visibility=page.get("visibility", True) if isinstance(page.get("visibility"), bool) else True,
                )
                pages_metadata.append(page_meta.model_dump())
            except Exception as e:
                print(f"Error processing page: {e}")
                continue

        return {
            "pages": pages_metadata,
            "count": len(pages_metadata),
        }

    def list_visuals(self, page_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List visuals across the report or for a specific page.

        Args:
            page_id: Optional page identifier filter

        Returns:
            Dictionary containing visuals and visual count
        """
        visuals = (
            self.parser.get_visuals(page_id)
            if page_id
            else self.parser.get_all_visuals()
        )

        visuals_metadata = []
        for visual in visuals:
            try:
                page_id_value = visual.get("page_id", "")
                raw_visual = visual.get("raw", {})
                visual_type = self._detect_visual_type(raw_visual)
                position = raw_visual.get("position", {})

                visual_meta = VisualMetadata(
                    visual_id=visual.get("visual_id", ""),
                    visual_name=raw_visual.get("name", ""),
                    visual_type=visual_type,
                    page_id=page_id_value,
                    title=raw_visual.get("title", ""),
                    x=position.get("x", 0),
                    y=position.get("y", 0),
                    width=position.get("width", 0),
                    height=position.get("height", 0),
                    bindings=raw_visual.get("bindings", {}),
                )
                visuals_metadata.append(visual_meta.model_dump())
            except Exception as e:
                print(f"Error processing visual: {e}")
                continue

        response: Dict[str, Any] = {
            "visuals": visuals_metadata,
            "count": len(visuals_metadata),
        }
        if page_id:
            response["page_id"] = page_id

        return response

    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables in the semantic model.

        Returns:
            Dictionary containing tables and table count
        """
        tables = self.parser.get_tables()

        tables_metadata = []
        for table in tables:
            try:
                table_meta = TableMetadata(
                    table_name=table.get("name", ""),
                    table_display_name=table.get("displayName", table.get("name", "")),
                    is_hidden=table.get("isHidden", False),
                    is_private=table.get("isPrivate", False),
                    description=table.get("description", ""),
                )
                tables_metadata.append(table_meta.model_dump())
            except Exception as e:
                print(f"Error processing table: {e}")
                continue

        return {
            "tables": tables_metadata,
            "count": len(tables_metadata),
        }

    def list_measures(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List all measures in the semantic model.

        Args:
            table_name: Optional filter by table name

        Returns:
            Dictionary containing measures and measure count
        """
        measures = self.parser.get_measures(table_name)

        measures_metadata = []
        for measure in measures:
            try:
                measure_meta = MeasureMetadata(
                    measure_name=measure.get("measure_name", measure.get("name", "")),
                    table_name=measure.get("table_name", ""),
                    expression=measure.get("expression", ""),
                    description=measure.get("description", ""),
                    format_string=measure.get("formatString", ""),
                    is_hidden=measure.get("isHidden", False),
                )
                measures_metadata.append(measure_meta.model_dump())
            except Exception as e:
                print(f"Error processing measure: {e}")
                continue

        return {
            "measures": measures_metadata,
            "count": len(measures_metadata),
            "table_filter": table_name,
        }

    def list_columns(self, table_name: str) -> Dict[str, Any]:
        """
        List all columns in a specific table.

        Args:
            table_name: Name of table

        Returns:
            Dictionary containing columns and column count
        """
        columns = self.parser.get_columns(table_name)

        columns_metadata = []
        for column in columns:
            try:
                column_meta = ColumnMetadata(
                    column_name=column.get("name", ""),
                    table_name=table_name,
                    data_type=column.get("dataType", "string"),
                    is_key=column.get("isKey", False),
                    description=column.get("description", ""),
                )
                columns_metadata.append(column_meta.model_dump())
            except Exception as e:
                print(f"Error processing column: {e}")
                continue

        return {
            "table_name": table_name,
            "columns": columns_metadata,
            "count": len(columns_metadata),
        }

    def get_visual_details(self, page_id: str, visual_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific visual.

        Args:
            page_id: Parent page identifier
            visual_id: Visual identifier

        Returns:
            Detailed visual information or error
        """
        visual = self.parser.get_visual_details(page_id, visual_id)

        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        visual_type = self._detect_visual_type(visual)

        return {
            "success": True,
            "visual_id": visual_id,
            "page_id": page_id,
            "visual_type": visual_type,
            "name": visual.get("name", ""),
            "title": visual.get("title", ""),
            "position": {
                "x": visual.get("x", 0),
                "y": visual.get("y", 0),
            },
            "size": {
                "width": visual.get("width", 0),
                "height": visual.get("height", 0),
            },
            "bindings": visual.get("bindings", {}),
            "properties": visual.get("properties", {}),
        }

    def get_table_details(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table.

        Args:
            table_name: Name of table

        Returns:
            Detailed table information or error
        """
        tables = self.parser.get_tables()
        table_info = next((t for t in tables if t.get("name") == table_name), None)

        if not table_info:
            return {
                "success": False,
                "error": f"Table not found: {table_name}",
            }

        columns = self.parser.get_columns(table_name)
        measures_list = self.parser.get_measures(table_name)

        return {
            "success": True,
            "table_name": table_name,
            "display_name": table_info.get("displayName", table_name),
            "description": table_info.get("description", ""),
            "is_hidden": table_info.get("isHidden", False),
            "column_count": len(columns),
            "measure_count": len(measures_list),
            "columns": [c.get("name") for c in columns],
            "measures": [m.get("name") for m in measures_list],
        }

    def get_measure_details(self, measure_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific measure.

        Args:
            measure_name: Name of measure

        Returns:
            Detailed measure information or error
        """
        measure = self.parser.get_measure_by_name(measure_name)

        if not measure:
            return {
                "success": False,
                "error": f"Measure not found: {measure_name}",
            }

        return {
            "success": True,
            "measure_name": measure_name,
            "table_name": measure.get("table_name", ""),
            "expression": measure.get("expression", ""),
            "description": measure.get("description", ""),
            "format_string": measure.get("formatString", ""),
            "is_hidden": measure.get("isHidden", False),
            "data_type": measure.get("dataType", ""),
        }

    def search_visuals(self, search_term: str) -> Dict[str, Any]:
        """
        Search for visuals by name or title.

        Args:
            search_term: Search term

        Returns:
            List of matching visuals
        """
        pages = self.parser.get_pages()
        results = []

        for page in pages:
            page_id = page.get("name", "")
            visuals = self.parser.get_visuals(page_id)

            for visual in visuals:
                if (
                    search_term.lower() in visual.get("name", "").lower()
                    or search_term.lower() in visual.get("title", "").lower()
                ):
                    results.append({
                        "page_id": page_id,
                        "page_name": page.get("displayName", page_id),
                        "visual_id": visual.get("visual_id", ""),
                        "visual_name": visual.get("name", ""),
                        "visual_title": visual.get("title", ""),
                    })

        return {
            "search_term": search_term,
            "results": results,
            "count": len(results),
        }

    def search_measures(self, search_term: str) -> Dict[str, Any]:
        """
        Search for measures by name or expression.

        Args:
            search_term: Search term

        Returns:
            List of matching measures
        """
        measures = self.parser.get_measures()
        results = []

        for measure in measures:
            if (
                search_term.lower() in measure.get("name", "").lower()
                or search_term.lower() in measure.get("expression", "").lower()
            ):
                results.append({
                    "measure_name": measure.get("name", ""),
                    "table_name": measure.get("table_name", ""),
                    "expression": measure.get("expression", ""),
                })

        return {
            "search_term": search_term,
            "results": results,
            "count": len(results),
        }

    def get_report_summary(self) -> Dict[str, Any]:
        """
        Get high-level summary of the entire report.

        Returns:
            Report summary statistics
        """
        pages = self.parser.get_pages()
        tables = self.parser.get_tables()
        measures = self.parser.get_measures()

        total_visuals = sum(len(self.parser.get_visuals(p.get("name"))) for p in pages)

        return {
            "pbip_root": str(self.pbip_root),
            "pages_count": len(pages),
            "visuals_count": total_visuals,
            "tables_count": len(tables),
            "measures_count": len(measures),
            "columns_count": sum(len(self.parser.get_columns(t.get("name"))) for t in tables),
            "page_names": [p.get("displayName", p.get("name")) for p in pages],
        }

    def _detect_visual_type(self, visual: Dict[str, Any]) -> VisualType:
        """
        Detect visual type from visual data.

        Args:
            visual: Visual data dictionary

        Returns:
            Detected visual type
        """
        # Try to detect from visual properties
        visual_type = ""
        if isinstance(visual, dict):
            visual_type = (
                visual.get("visualType")
                or visual.get("type")
                or visual.get("chartType")
                or (visual.get("visual") or {}).get("visualType")
                or ""
            )

        visual_type = str(visual_type).lower()

        if "card" in visual_type or "kpi" in visual_type:
            return VisualType.KPI
        elif "pie" in visual_type:
            return VisualType.PIE_CHART
        elif "bar" in visual_type:
            if "clustered" in visual_type:
                return VisualType.CLUSTERED_BAR
            return VisualType.BAR_CHART
        elif "column" in visual_type:
            if "clustered" in visual_type:
                return VisualType.CLUSTERED_COLUMN
            return VisualType.COLUMN_CHART
        elif "line" in visual_type:
            return VisualType.LINE_CHART
        elif "table" in visual_type:
            return VisualType.TABLE
        elif "matrix" in visual_type:
            return VisualType.MATRIX
        elif "slicer" in visual_type:
            return VisualType.SLICER
        else:
            return VisualType.UNKNOWN
