"""Context collector: Task specification and config."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from context_collectors.base import BaseContextCollector
    from utils.models import CheckerAgentRequest, ContextFragment
    from utils.paths import discover_project_paths
    from utils.text import condense_whitespace, truncate
except ImportError:
    from AutoGenChecker.context_collectors.base import BaseContextCollector
    from AutoGenChecker.utils.models import CheckerAgentRequest, ContextFragment
    from AutoGenChecker.utils.paths import discover_project_paths
    from AutoGenChecker.utils.text import condense_whitespace, truncate


class TaskSpecCollector(BaseContextCollector):
    """Gather configuration files tied to the requested checker."""

    name = "task_spec"

    def __init__(self, max_chars: int = 2000) -> None:
        self._max_chars = max_chars
        self._paths = discover_project_paths().ensure_exists()

    def collect(
        self, request: CheckerAgentRequest | None = None
    ) -> Iterable[ContextFragment]:  # type: ignore[override]
        if request is None:
            return []
        if not self._paths.check_modules_root:
            return []

        module_dir = self._paths.check_modules_root / request.module
        if not module_dir.exists():
            return []

        fragments: list[ContextFragment] = []
        fragments.extend(self._maybe_read_module_notes(module_dir))
        fragments.extend(self._maybe_read_item_config(module_dir, request))
        return fragments

    def _maybe_read_module_notes(self, module_dir: Path) -> list[ContextFragment]:
        for candidate in ("MIGRATION_SUMMARY.md", "README.md"):
            doc = module_dir / candidate
            if doc.exists():
                text = self._read(doc)
                if text:
                    return [
                        ContextFragment(
                            title=f"Module notes for {module_dir.name}",
                            content=truncate(text, max_chars=self._max_chars),
                            source=str(doc),
                            importance="medium",
                        )
                    ]
        return []

    def _maybe_read_item_config(
        self, module_dir: Path, request: CheckerAgentRequest
    ) -> list[ContextFragment]:
        items_dir = module_dir / "inputs" / "items"
        if not items_dir.exists():
            return []

        config_file = items_dir / f"{request.item_id}.yaml"
        if not config_file.exists():
            return []

        text = self._read(config_file)
        if not text:
            return []

        return [
            ContextFragment(
                title=f"Spec for {request.item_id}",
                content=condense_whitespace(
                    truncate(text, max_chars=self._max_chars)
                ),
                source=str(config_file),
                importance="high",
            )
        ]

    def _read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1", errors="ignore")
        except FileNotFoundError:
            return ""
