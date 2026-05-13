"""Centralized configuration loader for the Power BI MCP Agent project.

Loads environment values from the project .env file exactly once and exposes
validated configuration values to runtime components.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
REPORT_FOLDER_NAME = "Sales_report_PBIP.Report"
SEMANTIC_MODEL_FOLDER_NAME = "Sales_report_PBIP.SemanticModel"
PBIP_FILE_NAME = "Sales_report_PBIP.pbip"

# Load environment variables once at import time.
# If the process already has environment values set, they are preserved.
load_dotenv(dotenv_path=ENV_PATH, override=False)


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key, default)
    return value.strip() if isinstance(value, str) else value


def _resolve_path(path_value: Optional[str], default: Path) -> Path:
    if not path_value:
        return default

    path = Path(path_value)
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _parse_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for environment variable: {value}") from exc


class StartupValidationError(Exception):
    """Raised when startup configuration validation fails."""


OPENAI_API_KEY = _get_env("OPENAI_API_KEY")
OPENAI_MODEL = _get_env("OPENAI_MODEL", "gpt-4o")
PBIP_ROOT = _resolve_path(_get_env("PBIP_ROOT"), PROJECT_ROOT)
MCP_HOST = _get_env("MCP_HOST", "localhost")
MCP_PORT = _parse_int(_get_env("MCP_PORT", "8000"), 8000)

REPORT_FOLDER = PBIP_ROOT / REPORT_FOLDER_NAME
SEMANTIC_MODEL_FOLDER = PBIP_ROOT / SEMANTIC_MODEL_FOLDER_NAME
PBIP_FILE = PBIP_ROOT / PBIP_FILE_NAME


def validate_environment() -> Dict[str, Any]:
    """Validate required environment values and PBIP project structure."""
    errors: list[str] = []
    diagnostics: dict[str, Any] = {
        "OPENAI_API_KEY": bool(OPENAI_API_KEY),
        "OPENAI_MODEL": OPENAI_MODEL,
        "PBIP_ROOT": str(PBIP_ROOT),
        "REPORT_FOLDER": str(REPORT_FOLDER),
        "SEMANTIC_MODEL_FOLDER": str(SEMANTIC_MODEL_FOLDER),
        "PBIP_FILE": str(PBIP_FILE),
    }

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY must be set in environment or .env file.")

    if not OPENAI_MODEL:
        errors.append("OPENAI_MODEL must be set or default to 'gpt-4o'.")

    if not PBIP_ROOT.exists():
        errors.append(f"PBIP_ROOT path does not exist: {PBIP_ROOT}")

    if not REPORT_FOLDER.exists():
        errors.append(f"Report folder not found: {REPORT_FOLDER}")

    if not SEMANTIC_MODEL_FOLDER.exists():
        errors.append(f"Semantic model folder not found: {SEMANTIC_MODEL_FOLDER}")

    if not PBIP_FILE.exists():
        errors.append(f"PBIP file not found: {PBIP_FILE}")

    return {
        "success": len(errors) == 0,
        "errors": errors,
        "diagnostics": diagnostics,
    }


def startup_summary() -> str:
    """Return a formatted startup summary for validation results."""
    result = validate_environment()
    lines: list[str] = ["=" * 50, "Power BI MCP Agent Startup", "=" * 50, ""]

    if result["success"]:
        lines.append("[OK] OpenAI API Key Loaded")
        lines.append(f"[OK] Model: {OPENAI_MODEL}")
        lines.append(f"[OK] PBIP Project Found: {PBIP_ROOT}")
        lines.append(f"[OK] Report Folder Found: {REPORT_FOLDER}")
        lines.append(f"[OK] Semantic Model Found: {SEMANTIC_MODEL_FOLDER}")
        lines.append(f"[OK] PBIP file found: {PBIP_FILE}")
    else:
        lines.append("[ERROR] Startup validation failed with the following issues:")
        for error in result["errors"]:
            lines.append(f"  - {error}")

    lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)


def require_valid_environment() -> None:
    """Raise a StartupValidationError if the environment is invalid."""
    result = validate_environment()
    if not result["success"]:
        message = startup_summary()
        raise StartupValidationError(message)
