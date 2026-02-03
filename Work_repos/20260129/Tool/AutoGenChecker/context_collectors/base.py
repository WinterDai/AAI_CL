"""Base classes for context collection modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable
import sys
from pathlib import Path

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from utils.models import CheckerAgentRequest, ContextFragment
except ImportError:
    from AutoGenChecker.utils.models import CheckerAgentRequest, ContextFragment


class BaseContextCollector(ABC):
    """Collector that emits context fragments for prompt construction."""

    name: str = "base"

    @abstractmethod
    def collect(
        self, request: CheckerAgentRequest | None = None
    ) -> Iterable[ContextFragment]:
        """Return an iterable of context fragments."""

    def safe_collect(
        self, request: CheckerAgentRequest | None = None
    ) -> list[ContextFragment]:
        """Collect fragments, swallowing non-fatal exceptions."""

        fragments: list[ContextFragment] = []
        try:
            fragments.extend(self.collect(request))
        except FileNotFoundError:
            return []
        except Exception as exc:  # pragma: no cover - defensive logging hook
            fragments.append(
                ContextFragment(
                    title=f"{self.name} collector error",
                    content=str(exc),
                    source=self.name,
                    importance="low",
                )
            )
        return fragments
