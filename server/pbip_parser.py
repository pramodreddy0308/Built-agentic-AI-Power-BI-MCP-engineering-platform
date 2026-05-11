"""
PBIP Parser module for analyzing Power BI Project structure.

Parses PBIP files, extracts metadata, and provides utilities for navigating
the report and semantic model structures.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import PBIPStructure, VisualType


class PBIPParser:
    """Parser for Power BI PBIP project structure."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize PBIP parser.

        Args:
            project_root: Root path of the PBIP project. If omitted, uses the
                parent directory of this module via Path(__file__).resolve().parent.parent.

        Raises:
            ValueError: If project_root is not a valid PBIP project
        """
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parent.parent
        )
        self._validate_project_structure()
        self.pbip_structure = self._build_structure()

    def _validate_project_structure(self) -> None:
        """
        Validate that the project has required PBIP structure.

        Raises:
            ValueError: If required directories are missing
        """
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")

        self.report_folder = self.project_root / "Sales_report_PBIP.Report"
        self.semantic_model_folder = self.project_root / "Sales_report_PBIP.SemanticModel"

        if not self.report_folder.exists():
            raise ValueError(
                f"Report folder not found: {self.report_folder}. "
                "Ensure Sales_report_PBIP.Report exists under the project root."
            )

        if not self.semantic_model_folder.exists():
            raise ValueError(
                f"Semantic model folder not found: {self.semantic_model_folder}. "
                "Ensure Sales_report_PBIP.SemanticModel exists under the project root."
            )

    def _build_structure(self) -> PBIPStructure:
        """
        Build PBIPStructure object from project layout.

        Returns:
            PBIPStructure containing paths to all key components
        """
        pbip_file = next(self.project_root.glob("*.pbip"), None)

        return PBIPStructure(
            project_root=self.project_root,
            report_folder=self.report_folder,
            semantic_model_folder=self.semantic_model_folder,
            pbip_file=pbip_file,
        )

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Extract all pages from report.

        Returns:
            List of page metadata dictionaries
        """
        pages: List[Dict[str, Any]] = []
        pages_root = self.report_folder / "definition" / "pages"

        if not pages_root.exists():
            return pages

        for page_folder in sorted(pages_root.iterdir()):
            if not page_folder.is_dir():
                continue

            page_json = page_folder / "page.json"
            if not page_json.exists():
                continue

            try:
                with open(page_json, "r", encoding="utf-8") as f:
                    page_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            pages.append({
                "page_id": page_folder.name,
                "name": page_data.get("name", page_folder.name),
                "displayName": page_data.get("displayName", page_data.get("name", page_folder.name)),
                "visibility": page_data.get("visibility", True),
                "raw": page_data,
            })

        return pages

    def get_page_details(self, page_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific page.

        Args:
            page_id: Unique page identifier

        Returns:
            Page details or None if not found
        """
        page_folder = (
            self.pbip_structure.report_folder / "definition" / "pages" / page_id
        )

        if not page_folder.exists():
            return None

        page_json = page_folder / "page.json"
        if page_json.exists():
            with open(page_json, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def get_visuals(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Extract all visuals from a specific page.

        Args:
            page_id: Unique page identifier

        Returns:
            List of visual metadata dictionaries
        """
        visuals: List[Dict[str, Any]] = []
        visuals_root = (
            self.report_folder / "definition" / "pages" / page_id / "visuals"
        )

        if not visuals_root.exists():
            return visuals

        for visual_folder in sorted(visuals_root.iterdir()):
            if not visual_folder.is_dir():
                continue

            visual_json = visual_folder / "visual.json"
            if not visual_json.exists():
                continue

            try:
                with open(visual_json, "r", encoding="utf-8") as f:
                    visual_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            visuals.append({
                "page_id": page_id,
                "visual_id": visual_folder.name,
                "visual_type": self._detect_visual_type(visual_data),
                "raw": visual_data,
            })

        return visuals

    def get_visual_details(self, page_id: str, visual_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific visual.

        Args:
            page_id: Parent page ID
            visual_id: Unique visual identifier

        Returns:
            Visual details or None if not found
        """
        visual_json = (
            self.report_folder
            / "definition"
            / "pages"
            / page_id
            / "visuals"
            / visual_id
            / "visual.json"
        )

        if not visual_json.exists():
            return None

        try:
            with open(visual_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        return {
            "page_id": page_id,
            "visual_id": visual_id,
            "visual_type": self._detect_visual_type(data),
            "raw": data,
        }

    def get_all_visuals(self) -> List[Dict[str, Any]]:
        """
        Recursively discover all visuals across every page in the report.

        Returns:
            List of visual metadata dictionaries with page and visual identifiers.
        """
        visuals: List[Dict[str, Any]] = []
        pages_root = self.report_folder / "definition" / "pages"

        if not pages_root.exists():
            return visuals

        for visual_json in pages_root.rglob("visual.json"):
            try:
                with open(visual_json, "r", encoding="utf-8") as f:
                    visual_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            visual_id = visual_json.parent.name
            page_id = ""
            if "pages" in visual_json.parts:
                parts = visual_json.parts
                page_index = parts.index("pages")
                if page_index + 1 < len(parts):
                    page_id = parts[page_index + 1]

            visuals.append(
                {
                    "page_id": page_id,
                    "visual_id": visual_id,
                    "visual_type": self._detect_visual_type(visual_data),
                    "raw": visual_data,
                }
            )

        return visuals

    def _detect_visual_type(self, visual_data: Dict[str, Any]) -> str:
        """
        Detect a visual type from the loaded visual definition.

        Args:
            visual_data: Raw visual JSON data

        Returns:
            Visual type identifier if available, otherwise empty string
        """
        if not isinstance(visual_data, dict):
            return ""

        return (
            visual_data.get("type")
            or visual_data.get("visualType")
            or visual_data.get("chartType")
            or ""
        )

    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Extract all tables from the semantic model.

        Returns:
            List of table metadata dictionaries
        """
        tables: List[Dict[str, Any]] = []
        tables_folder = self.semantic_model_folder / "definition" / "tables"

        if not tables_folder.exists():
            return tables

        for table_file in sorted(tables_folder.glob("*.tmdl")):
            table_data = self._parse_tmdl_file(table_file)
            if not table_data:
                continue
            tables.append(
                {
                    "name": table_data.get("name", table_file.stem),
                    "file_name": table_file.name,
                    "measures": table_data.get("measures", []),
                    "columns": table_data.get("columns", []),
                }
            )

        return tables

    def get_measures(self, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract measures from the semantic model.

        Args:
            table_name: Optional filter by table name

        Returns:
            List of measure metadata dictionaries
        """
        measures: List[Dict[str, Any]] = []
        tables = self.get_tables()

        for table in tables:
            if table_name and table["name"] != table_name:
                continue

            for measure in table.get("measures", []):
                measures.append(
                    {
                        "table_name": table.get("name", ""),
                        "measure_name": measure.get("name", ""),
                        "expression": measure.get("expression", ""),
                        "description": measure.get("description", ""),
                        "raw": measure,
                    }
                )

        return measures

    def get_measure_by_name(self, measure_name: str) -> Optional[Dict[str, Any]]:
        """
        Find measure by name.

        Args:
            measure_name: Name of measure to find

        Returns:
            Measure metadata or None
        """
        measures = self.get_measures()
        for measure in measures:
            if measure.get("measure_name") == measure_name or measure.get("name") == measure_name:
                return measure
        return None

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get columns from a specific table.

        Args:
            table_name: Name of table

        Returns:
            List of column metadata
        """
        table_file = (
            self.pbip_structure.semantic_model_folder
            / "definition"
            / "tables"
            / f"{table_name}.tmdl"
        )

        if not table_file.exists():
            return []

        table_data = self._parse_tmdl_file(table_file)
        return table_data.get("columns", []) if table_data else []

    def _parse_tmdl_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a TMDL file and extract structured table and measure information.

        Args:
            file_path: Path to TMDL file

        Returns:
            Parsed data or None if parsing fails
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            parsed: Dict[str, Any] = {"name": file_path.stem}
            parsed["measures"] = self._extract_tmdl_measures(content)
            parsed["columns"] = self._extract_tmdl_columns(content)
            return parsed

        except (OSError, UnicodeDecodeError) as exc:
            print(f"Error parsing TMDL file {file_path}: {exc}")
            return None

    def _extract_tmdl_measures(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract measure definitions from TMDL content.

        Args:
            content: TMDL file content

        Returns:
            List of measures
        """
        measures: List[Dict[str, Any]] = []
        pattern = re.compile(
            r"^measure\s+(?:\"([^\"]+)\"|'([^']+)'|([\w\_\-\.]+))\s*=\s*(.+)$",
            re.IGNORECASE,
        )

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("--"):
                continue

            match = pattern.match(line)
            if not match:
                continue

            measure_name = match.group(1) or match.group(2) or match.group(3) or ""
            expression = match.group(4).strip()
            measures.append(
                {
                    "name": measure_name,
                    "expression": expression,
                }
            )

        return measures

    def _extract_tmdl_columns(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract column definitions from TMDL content.

        Args:
            content: TMDL file content

        Returns:
            List of columns
        """
        columns: List[Dict[str, Any]] = []
        pattern = re.compile(r"^column\s+([\w\_\-\.]+)", re.IGNORECASE)

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//") or line.startswith("--"):
                continue

            match = pattern.match(line)
            if not match:
                continue

            columns.append({"name": match.group(1).strip()})

        return columns

    def get_report_metadata(self) -> Dict[str, Any]:
        """
        Get overall report metadata.

        Returns:
            Report metadata dictionary
        """
        definition_file = (
            self.pbip_structure.report_folder / "definition" / "report.json"
        )

        if definition_file.exists():
            with open(definition_file, "r", encoding="utf-8") as f:
                return json.load(f)

        return {}

    def get_semantic_model_metadata(self) -> Dict[str, Any]:
        """
        Get semantic model metadata.

        Returns:
            Model metadata dictionary
        """
        definition_file = (
            self.pbip_structure.semantic_model_folder / "definition" / "model.tmdl"
        )

        if definition_file.exists():
            return self._parse_tmdl_file(definition_file) or {}

        return {}

    def save_visual(
        self, page_id: str, visual_id: str, visual_data: Dict[str, Any]
    ) -> bool:
        """
        Save visual changes back to file.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier
            visual_data: Updated visual data

        Returns:
            True if successful, False otherwise
        """
        visual_json = (
            self.pbip_structure.report_folder
            / "definition"
            / "pages"
            / page_id
            / "visuals"
            / visual_id
            / "visual.json"
        )

        try:
            visual_json.parent.mkdir(parents=True, exist_ok=True)
            with open(visual_json, "w", encoding="utf-8") as f:
                json.dump(visual_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving visual: {e}")
            return False

    def save_page(self, page_id: str, page_data: Dict[str, Any]) -> bool:
        """
        Save page changes back to file.

        Args:
            page_id: Page identifier
            page_data: Updated page data

        Returns:
            True if successful, False otherwise
        """
        page_json = (
            self.pbip_structure.report_folder
            / "definition"
            / "pages"
            / page_id
            / "page.json"
        )

        try:
            page_json.parent.mkdir(parents=True, exist_ok=True)
            with open(page_json, "w", encoding="utf-8") as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving page: {e}")
            return False

    def save_table_definition(self, table_name: str, table_data: Dict[str, Any]) -> bool:
        """
        Save table definition changes.

        Args:
            table_name: Table name
            table_data: Updated table data

        Returns:
            True if successful, False otherwise
        """
        table_file = (
            self.pbip_structure.semantic_model_folder
            / "definition"
            / "tables"
            / f"{table_name}.tmdl"
        )

        try:
            table_file.parent.mkdir(parents=True, exist_ok=True)
            # TMDL format handling
            tmdl_content = self._dict_to_tmdl(table_data)
            with open(table_file, "w", encoding="utf-8") as f:
                f.write(tmdl_content)
            return True
        except Exception as e:
            print(f"Error saving table definition: {e}")
            return False

    def _dict_to_tmdl(self, data: Dict[str, Any]) -> str:
        """
        Convert dictionary data to TMDL format (simplified).

        Args:
            data: Data to convert

        Returns:
            TMDL formatted string
        """
        lines = []

        # Basic TMDL structure
        if "name" in data:
            lines.append(f"table {data['name']}")
            lines.append("{")

            if "measures" in data:
                for measure in data["measures"]:
                    if isinstance(measure, dict):
                        name = measure.get("name", "")
                        expr = measure.get("expression", "")
                        lines.append(f"  measure {name} = {expr}")

            if "columns" in data:
                for column in data["columns"]:
                    if isinstance(column, dict):
                        name = column.get("name", "")
                        lines.append(f"  column {name}")

            lines.append("}")

        return "\n".join(lines)
