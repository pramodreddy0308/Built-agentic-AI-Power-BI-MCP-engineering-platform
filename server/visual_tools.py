"""
Visual tools for modifying report visuals and layouts.

Provides MCP-compatible functions for adding/updating KPI cards, replacing
visuals, adjusting positions and sizes, and other visual modifications.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import KPICardConfig, VisualType
from .pbip_parser import PBIPParser


class VisualTools:
    """Tools for visual modifications."""

    def __init__(self, pbip_root: Path):
        """
        Initialize visual tools.

        Args:
            pbip_root: Root path of PBIP project
        """
        self.pbip_root = Path(pbip_root)
        self.parser = PBIPParser(self.pbip_root)

    def add_kpi_card(
        self,
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
    ) -> Dict[str, Any]:
        """
        Add a KPI card visual to a page.

        Args:
            page_id: Target page ID
            title: KPI title
            measure_name: Measure to display
            table_name: Measure's table
            x: X position (pixels)
            y: Y position (pixels)
            width: Card width
            height: Card height
            display_units: Display units (Auto, Thousands, Millions, Billions)
            color: Card color (hex code)

        Returns:
            Operation result
        """
        # Validate page exists
        page = self.parser.get_page_details(page_id)
        if not page:
            return {
                "success": False,
                "error": f"Page not found: {page_id}",
            }

        # Validate measure exists
        measure = self.parser.get_measure_by_name(measure_name)
        if not measure:
            return {
                "success": False,
                "error": f"Measure not found: {measure_name}",
            }

        # Generate visual ID
        visual_id = str(uuid.uuid4().hex[:20])

        # Create KPI visual configuration
        kpi_config = KPICardConfig(
            title=title,
            measure_name=measure_name,
            table_name=table_name,
            display_units=display_units,
            color=color,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        # Build visual JSON structure
        visual_data = self._build_kpi_visual(kpi_config, visual_id)

        # Save visual to file
        success = self.parser.save_visual(page_id, visual_id, visual_data)

        if not success:
            return {
                "success": False,
                "error": f"Failed to save visual to page {page_id}",
            }

        return {
            "success": True,
            "message": f"KPI card added successfully: {title}",
            "visual_id": visual_id,
            "page_id": page_id,
            "visual_config": kpi_config.model_dump(),
        }

    def update_visual_title(
        self, page_id: str, visual_id: str, new_title: str
    ) -> Dict[str, Any]:
        """
        Update the title of a visual.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier
            new_title: New title text

        Returns:
            Operation result
        """
        # Get current visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Update title
        visual["title"] = new_title

        # Save changes
        success = self.parser.save_visual(page_id, visual_id, visual)

        if not success:
            return {
                "success": False,
                "error": "Failed to save visual changes",
            }

        return {
            "success": True,
            "message": f"Visual title updated: {new_title}",
            "visual_id": visual_id,
            "page_id": page_id,
        }

    def move_visual(
        self, page_id: str, visual_id: str, x: float, y: float
    ) -> Dict[str, Any]:
        """
        Move a visual to a new position.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier
            x: New X position
            y: New Y position

        Returns:
            Operation result
        """
        # Get current visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Update position
        visual["x"] = x
        visual["y"] = y

        # Save changes
        success = self.parser.save_visual(page_id, visual_id, visual)

        if not success:
            return {
                "success": False,
                "error": "Failed to save visual position",
            }

        return {
            "success": True,
            "message": f"Visual moved to ({x}, {y})",
            "visual_id": visual_id,
            "page_id": page_id,
            "position": {"x": x, "y": y},
        }

    def resize_visual(
        self,
        page_id: str,
        visual_id: str,
        width: float,
        height: float,
    ) -> Dict[str, Any]:
        """
        Resize a visual.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier
            width: New width
            height: New height

        Returns:
            Operation result
        """
        # Get current visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Update size
        visual["width"] = width
        visual["height"] = height

        # Save changes
        success = self.parser.save_visual(page_id, visual_id, visual)

        if not success:
            return {
                "success": False,
                "error": "Failed to save visual size",
            }

        return {
            "success": True,
            "message": f"Visual resized to {width}x{height}",
            "visual_id": visual_id,
            "page_id": page_id,
            "size": {"width": width, "height": height},
        }

    def replace_visual(
        self,
        page_id: str,
        visual_id: str,
        new_visual_type: str,
        preserve_bindings: bool = True,
    ) -> Dict[str, Any]:
        """
        Replace a visual with a different type.

        Args:
            page_id: Parent page ID
            visual_id: Visual identifier
            new_visual_type: New visual type (e.g., 'clusteredBar', 'lineChart')
            preserve_bindings: Whether to preserve data bindings

        Returns:
            Operation result
        """
        # Get current visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Store bindings if preserving
        old_bindings = visual.get("bindings", {}) if preserve_bindings else {}

        # Create new visual with same properties
        new_visual = visual.copy()
        new_visual["visualType"] = new_visual_type

        # Restore bindings if applicable
        if preserve_bindings and old_bindings:
            new_visual["bindings"] = old_bindings

        # Save changes
        success = self.parser.save_visual(page_id, visual_id, new_visual)

        if not success:
            return {
                "success": False,
                "error": "Failed to replace visual",
            }

        return {
            "success": True,
            "message": f"Visual replaced with type: {new_visual_type}",
            "visual_id": visual_id,
            "page_id": page_id,
            "old_type": visual.get("visualType", "unknown"),
            "new_type": new_visual_type,
            "bindings_preserved": preserve_bindings,
        }

    def duplicate_visual(
        self, page_id: str, visual_id: str, offset_x: float = 300
    ) -> Dict[str, Any]:
        """
        Duplicate a visual on the same page.

        Args:
            page_id: Parent page ID
            visual_id: Visual to duplicate
            offset_x: X offset for duplicated visual

        Returns:
            Operation result
        """
        # Get source visual
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Create duplicate
        new_visual_id = str(uuid.uuid4().hex[:20])
        duplicated = visual.copy()
        duplicated["visual_id"] = new_visual_id
        duplicated["x"] = visual.get("x", 0) + offset_x
        duplicated["name"] = f"{visual.get('name', 'Visual')} (2)"

        # Save duplicate
        success = self.parser.save_visual(page_id, new_visual_id, duplicated)

        if not success:
            return {
                "success": False,
                "error": "Failed to duplicate visual",
            }

        return {
            "success": True,
            "message": f"Visual duplicated successfully",
            "original_visual_id": visual_id,
            "new_visual_id": new_visual_id,
            "page_id": page_id,
        }

    def delete_visual(self, page_id: str, visual_id: str) -> Dict[str, Any]:
        """
        Delete a visual from a page.

        Args:
            page_id: Parent page ID
            visual_id: Visual to delete

        Returns:
            Operation result
        """
        # Verify visual exists
        visual = self.parser.get_visual_details(page_id, visual_id)
        if not visual:
            return {
                "success": False,
                "error": f"Visual not found: {page_id}/{visual_id}",
            }

        # Delete visual file
        visual_folder = (
            self.pbip_root
            / f"{self.pbip_root.name}.Report"
            / "definition"
            / "pages"
            / page_id
            / "visuals"
            / visual_id
        )

        try:
            import shutil

            if visual_folder.exists():
                shutil.rmtree(visual_folder)

            return {
                "success": True,
                "message": f"Visual deleted successfully",
                "visual_id": visual_id,
                "page_id": page_id,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete visual: {str(e)}",
            }

    def batch_update_visuals(
        self,
        page_id: str,
        visual_updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update multiple visuals in batch.

        Args:
            page_id: Parent page ID
            visual_updates: List of visual update specifications

        Returns:
            Batch operation result
        """
        results = []

        for update in visual_updates:
            visual_id = update.get("visual_id")
            if not visual_id:
                results.append({
                    "visual_id": None,
                    "success": False,
                    "error": "visual_id is required",
                })
                continue

            # Get visual
            visual = self.parser.get_visual_details(page_id, visual_id)
            if not visual:
                results.append({
                    "visual_id": visual_id,
                    "success": False,
                    "error": "Visual not found",
                })
                continue

            # Apply updates
            if "title" in update:
                visual["title"] = update["title"]
            if "x" in update and "y" in update:
                visual["x"] = update["x"]
                visual["y"] = update["y"]
            if "width" in update and "height" in update:
                visual["width"] = update["width"]
                visual["height"] = update["height"]

            # Save visual
            success = self.parser.save_visual(page_id, visual_id, visual)
            results.append({
                "visual_id": visual_id,
                "success": success,
                "message": "Visual updated" if success else "Failed to save visual",
            })

        return {
            "success": all(r.get("success") for r in results),
            "batch_size": len(visual_updates),
            "results": results,
        }

    def _build_kpi_visual(self, config: KPICardConfig, visual_id: str) -> Dict[str, Any]:
        """
        Build KPI visual JSON structure.

        Args:
            config: KPI configuration
            visual_id: Visual identifier

        Returns:
            Visual JSON structure
        """
        return {
            "visual_id": visual_id,
            "name": config.title,
            "title": config.title,
            "visualType": "kpi",
            "x": config.x,
            "y": config.y,
            "width": config.width,
            "height": config.height,
            "bindings": {
                "measure": {
                    "table": config.table_name,
                    "column": config.measure_name,
                },
            },
            "properties": {
                "displayUnits": config.display_units,
                "color": config.color,
                "showTitle": True,
                "titleFontSize": 12,
            },
        }

    def get_visual_layout_info(self, page_id: str) -> Dict[str, Any]:
        """
        Get information about visual layout on a page.

        Args:
            page_id: Page identifier

        Returns:
            Layout information
        """
        visuals = self.parser.get_visuals(page_id)

        # Calculate layout statistics
        if not visuals:
            return {
                "page_id": page_id,
                "visual_count": 0,
                "total_area": 0,
                "layout_efficiency": 0,
            }

        positions = [
            {
                "visual_id": v.get("visual_id"),
                "x": v.get("x", 0),
                "y": v.get("y", 0),
                "width": v.get("width", 0),
                "height": v.get("height", 0),
                "area": v.get("width", 0) * v.get("height", 0),
            }
            for v in visuals
        ]

        total_area = sum(p["area"] for p in positions)

        return {
            "page_id": page_id,
            "visual_count": len(visuals),
            "total_area": total_area,
            "visuals": positions,
        }

    def auto_arrange_visuals(
        self,
        page_id: str,
        columns: int = 2,
        padding: float = 20,
    ) -> Dict[str, Any]:
        """
        Auto-arrange visuals on a page in grid layout.

        Args:
            page_id: Page identifier
            columns: Number of columns
            padding: Padding between visuals

        Returns:
            Operation result
        """
        visuals = self.parser.get_visuals(page_id)

        if not visuals:
            return {
                "success": False,
                "error": "No visuals found on page",
            }

        # Calculate grid positions
        results = []
        for idx, visual in enumerate(visuals):
            visual_id = visual.get("visual_id")

            row = idx // columns
            col = idx % columns

            # Position calculations
            x = col * (300 + padding)
            y = row * (300 + padding)

            # Move visual
            result = self.move_visual(page_id, visual_id, x, y)
            results.append(result)

        return {
            "success": all(r.get("success") for r in results),
            "message": f"Arranged {len(visuals)} visuals in {columns} columns",
            "visuals_arranged": len(results),
        }
