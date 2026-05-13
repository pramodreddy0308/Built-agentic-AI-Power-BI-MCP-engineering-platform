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
        Get detailed information for a specific visual with semantic metadata.

        Extracts title, visual type, position, bindings, measures, and categories.

        Args:
            page_id: Parent page ID
            visual_id: Unique visual identifier

        Returns:
            Rich visual metadata dict or None if not found
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

        # Extract semantic information
        visual_type = self._detect_visual_type(data)
        title = self._extract_visual_title(data)
        bindings = self._extract_visual_bindings(data)

        # Get page display name
        page_details = self.get_page_details(page_id)
        page_name = ""
        if page_details and isinstance(page_details, dict):
            page_name = page_details.get("displayName", page_details.get("name", ""))

        # Extract position
        position = data.get("position", {})
        pos_dict = {}
        if isinstance(position, dict):
            pos_dict = {
                "x": position.get("x", 0),
                "y": position.get("y", 0),
                "width": position.get("width", 0),
                "height": position.get("height", 0),
            }

        return {
            "visual_id": visual_id,
            "visual_type": visual_type,
            "title": title,
            "page_id": page_id,
            "page_name": page_name,
            "position": pos_dict,
            "measures": bindings.get("measures", []),
            "categories": bindings.get("categories", []),
            "raw": data,
        }

    def get_all_visuals(self) -> List[Dict[str, Any]]:
        """
        Recursively discover all visuals across every page with semantic metadata.

        Returns:
            List of rich visual metadata dicts with type, title, bindings, position.
        """
        visuals: List[Dict[str, Any]] = []
        pages_root = self.report_folder / "definition" / "pages"

        if not pages_root.exists():
            return visuals

        # Cache page details for reuse
        page_cache: Dict[str, Optional[Dict[str, Any]]] = {}

        for visual_json in pages_root.rglob("visual.json"):
            try:
                with open(visual_json, "r", encoding="utf-8") as f:
                    visual_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            # Extract page_id from path
            visual_id = visual_json.parent.name
            page_id = ""
            if "pages" in visual_json.parts:
                parts = visual_json.parts
                page_index = parts.index("pages")
                if page_index + 1 < len(parts):
                    page_id = parts[page_index + 1]

            # Extract semantic information
            visual_type = self._detect_visual_type(visual_data)
            title = self._extract_visual_title(visual_data)
            bindings = self._extract_visual_bindings(visual_data)

            # Get page display name (with caching)
            page_name = ""
            if page_id:
                if page_id not in page_cache:
                    page_details = self.get_page_details(page_id)
                    page_cache[page_id] = page_details
                page_details = page_cache[page_id]
                if page_details and isinstance(page_details, dict):
                    page_name = page_details.get(
                        "displayName", page_details.get("name", "")
                    )

            # Extract position
            position = visual_data.get("position", {})
            pos_dict = {}
            if isinstance(position, dict):
                pos_dict = {
                    "x": position.get("x", 0),
                    "y": position.get("y", 0),
                    "width": position.get("width", 0),
                    "height": position.get("height", 0),
                }

            visuals.append(
                {
                    "visual_id": visual_id,
                    "visual_type": visual_type,
                    "title": title,
                    "page_id": page_id,
                    "page_name": page_name,
                    "position": pos_dict,
                    "measures": bindings.get("measures", []),
                    "categories": bindings.get("categories", []),
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

        # Check nested visual structure first
        visual_obj = visual_data.get("visual", {})
        if isinstance(visual_obj, dict):
            visual_type = visual_obj.get("visualType", "")
            if visual_type:
                return visual_type

        return (
            visual_data.get("type")
            or visual_data.get("visualType")
            or visual_data.get("chartType")
            or ""
        )

    def _extract_visual_title(self, visual_data: Dict[str, Any]) -> str:
        """
        Extract visual title from nested visual definition.

        Searches multiple locations for title text:
        - visual.name
        - visual.objects.title
        - position.name
        - name field

        Args:
            visual_data: Raw visual JSON data

        Returns:
            Title string, or empty if not found
        """
        if not isinstance(visual_data, dict):
            return ""

        # Try direct name field
        if "name" in visual_data:
            return str(visual_data["name"])

        # Try nested visual object
        visual_obj = visual_data.get("visual", {})
        if isinstance(visual_obj, dict) and "name" in visual_obj:
            return str(visual_obj["name"])

        # Try objects section (text content)
        objects = visual_obj.get("objects", {})
        if isinstance(objects, dict):
            # Look for title in general properties
            general = objects.get("general", [])
            if isinstance(general, list) and len(general) > 0:
                props = general[0].get("properties", {})
                if "title" in props:
                    return str(props["title"])
            # Look in paragraphs (for textbox)
            paragraphs = objects.get("paragraphs", [])
            if isinstance(paragraphs, list) and len(paragraphs) > 0:
                first_para = paragraphs[0]
                if isinstance(first_para, dict):
                    text_runs = first_para.get("textRuns", [])
                    if isinstance(text_runs, list) and len(text_runs) > 0:
                        return str(text_runs[0].get("value", ""))

        return ""

    def _extract_visual_bindings(self, visual_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Extract measures and categories from visual query state.

        Inspects the queryState structure and extracts projections,
        mapping queryRef/displayName to measures and categories.

        Args:
            visual_data: Raw visual JSON data

        Returns:
            Dict with 'measures' and 'categories' lists
        """
        result: Dict[str, List[str]] = {"measures": [], "categories": []}

        if not isinstance(visual_data, dict):
            return result

        # Navigate to queryState
        visual_obj = visual_data.get("visual", {})
        if not isinstance(visual_obj, dict):
            return result

        query = visual_obj.get("query", {})
        if not isinstance(query, dict):
            return result

        query_state = query.get("queryState", {})
        if not isinstance(query_state, dict):
            return result

        # Extract from different query state sections
        for section_name, projections in query_state.items():
            if not isinstance(projections, dict):
                continue

            section_projections = projections.get("projections", [])
            if not isinstance(section_projections, list):
                continue

            for proj in section_projections:
                if not isinstance(proj, dict):
                    continue

                # Get display name or queryRef
                display_name = proj.get("displayName", "")
                native_query_ref = proj.get("nativeQueryRef", "")
                query_ref = proj.get("queryRef", "")

                # Prefer displayName, fallback to nativeQueryRef, then queryRef
                label = display_name or native_query_ref or query_ref or ""

                if not label:
                    continue

                # Categorize as measure or category based on field type
                field_obj = proj.get("field", {})
                if not isinstance(field_obj, dict):
                    result["categories"].append(label)
                    continue

                # Check if it's a measure (Aggregation) or category (Column/HierarchyLevel)
                if "Measure" in field_obj or "Aggregation" in field_obj:
                    result["measures"].append(label)
                else:
                    result["categories"].append(label)

        return result

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
