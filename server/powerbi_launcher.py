import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


DEFAULT_PBIDESKTOP_PATHS = [
    Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    / "Microsoft Power BI Desktop"
    / "bin"
    / "PBIDesktop.exe",
    Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    / "Microsoft Power BI Desktop"
    / "bin"
    / "PBIDesktop.exe",
    Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    / "Microsoft Power BI Desktop"
    / "PBIDesktop.exe",
    Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    / "Microsoft Power BI Desktop"
    / "PBIDesktop.exe",
]


def _find_pbip_file(project_root: Optional[Path] = None) -> Optional[Path]:
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parent.parent
    )

    if not root.exists():
        logger.error("Project root does not exist: %s", root)
        return None

    candidate = root / "Sales_report_PBIP.pbip"
    if candidate.exists():
        logger.info("Found PBIP file: %s", candidate)
        return candidate

    pbip_files = list(root.glob("*.pbip"))
    if not pbip_files:
        pbip_files = list(root.rglob("*.pbip"))

    if not pbip_files:
        logger.warning("No PBIP files found under %s", root)
        return None

    pbip_files.sort(key=lambda path: path.name)
    selected = pbip_files[0]
    logger.info("Using PBIP file: %s", selected)
    return selected


def _find_pbid_executable() -> Optional[Path]:
    executable_path = shutil.which("PBIDesktop.exe")
    if executable_path:
        path = Path(executable_path)
        logger.info("Found PBIDesktop.exe on PATH: %s", path)
        return path

    for candidate in DEFAULT_PBIDESKTOP_PATHS:
        if candidate.exists():
            logger.info("Found PBIDesktop.exe at default location: %s", candidate)
            return candidate

    logger.warning("PBIDesktop.exe not found in default locations")
    return None


def _terminate_existing_pbid() -> Tuple[bool, str]:
    logger.info("Attempting to terminate existing Power BI Desktop instances")
    try:
        result = subprocess.run(
            ["taskkill", "/IM", "PBIDesktop.exe", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        logger.error("taskkill command not available: %s", exc)
        return False, str(exc)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.returncode == 0:
        logger.info("Terminated Power BI Desktop: %s", stdout)
        return True, stdout

    if "no instance" in stderr.lower() or "not found" in stderr.lower():
        logger.info("No running Power BI Desktop instance found: %s", stderr)
        return True, stderr

    logger.error("Failed to terminate Power BI Desktop: %s", stderr or stdout)
    return False, stderr or stdout


def _launch_pbid(executable: Path, report_path: Path) -> Dict[str, Any]:
    if not executable.exists():
        message = f"PBIDesktop.exe not found at {executable}"
        logger.error(message)
        return {"success": False, "error": message, "report": str(report_path)}

    if not report_path.exists():
        message = f"PBIP report not found: {report_path}"
        logger.error(message)
        return {"success": False, "error": message, "report": str(report_path)}

    try:
        logger.info("Launching Power BI Desktop: %s %s", executable, report_path)
        subprocess.Popen([str(executable), str(report_path)], shell=False)
        return {"success": True, "report": str(report_path)}
    except Exception as exc:
        message = f"Failed to launch Power BI Desktop: {exc}"
        logger.exception(message)
        return {"success": False, "error": message, "report": str(report_path)}


def open_powerbi_report(
    project_root: Optional[Path] = None,
    close_existing: bool = False,
) -> Dict[str, Any]:
    """
    Open the PBIP report in Power BI Desktop.

    Args:
        project_root: Root path of the agent project.
        close_existing: If True, terminate existing Power BI Desktop instances first.

    Returns:
        Structured result with success state and report path.
    """
    root = (
        Path(project_root).resolve()
        if project_root is not None
        else Path(__file__).resolve().parent.parent
    )

    report_path = _find_pbip_file(root)
    if report_path is None:
        return {"success": False, "error": "PBIP file not found", "report": ""}

    executable = _find_pbid_executable()
    if executable is None:
        return {"success": False, "error": "PBIDesktop.exe not found", "report": str(report_path)}

    if close_existing:
        terminated, detail = _terminate_existing_pbid()
        if not terminated:
            return {
                "success": False,
                "error": f"Unable to terminate existing Power BI Desktop: {detail}",
                "report": str(report_path),
            }

    return _launch_pbid(executable, report_path)


def restart_powerbi_report(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Restart Power BI Desktop and reopen the PBIP report.

    Args:
        project_root: Root path of the agent project.

    Returns:
        Structured result with success state and report path.
    """
    result = open_powerbi_report(project_root=project_root, close_existing=True)
    if not result.get("success"):
        logger.error("Restart failed: %s", result.get("error"))
    else:
        logger.info("Power BI report restarted successfully: %s", result.get("report"))
    return result
