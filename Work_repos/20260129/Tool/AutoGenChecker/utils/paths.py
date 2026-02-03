"""Path utilities for locating project resources."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Resolved directories that the agent needs to access."""

    workspace_root: Path
    autogen_root: Path
    check_modules_root: Path | None
    collect_info_root: Path | None
    work_root: Path | None

    def ensure_exists(self) -> "ProjectPaths":
        """Return self if all required paths exist; raises otherwise."""

        if not self.workspace_root.exists():
            raise FileNotFoundError(f"Workspace root missing: {self.workspace_root}")
        if not self.autogen_root.exists():
            raise FileNotFoundError(f"AutoGenChecker root missing: {self.autogen_root}")
        return self


@lru_cache(maxsize=1)
def discover_project_paths() -> ProjectPaths:
    """Discover key folders starting from this module location."""

    current = Path(__file__).resolve()
    autogen_root = current.parent.parent

    workspace_root = _find_workspace_root(start=current)
    check_modules_root = _optional_dir(workspace_root / "Check_modules")
    collect_info_root = _optional_dir(workspace_root / "CollectInfo")
    work_root = _optional_dir(workspace_root / "Work")

    return ProjectPaths(
        workspace_root=workspace_root,
        autogen_root=autogen_root,
        check_modules_root=check_modules_root,
        collect_info_root=collect_info_root,
        work_root=work_root,
    )


def _find_workspace_root(start: Path) -> Path:
    """Walk up ancestors until a folder containing project markers is found."""

    # Starting from Tool/AutoGenChecker/utils/paths.py
    # Find the directory containing Check_modules (the CHECKLIST directory)
    for candidate in [start] + list(start.parents):
        if (candidate / "Check_modules").exists():
            return candidate
    
    # Fallback - go up to CHECKLIST_V3 then into CHECKLIST
    # paths.py is at Tool/AutoGenChecker/utils/paths.py
    # parents[0] = Tool/AutoGenChecker/utils
    # parents[1] = Tool/AutoGenChecker
    # parents[2] = Tool
    # parents[3] = CHECKLIST_V3
    return start.parents[3] / "CHECKLIST"


def _optional_dir(path: Path) -> Path | None:
    return path if path.exists() else None
