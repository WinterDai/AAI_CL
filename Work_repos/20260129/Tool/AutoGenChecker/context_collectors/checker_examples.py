"""Collectors that surface existing checker implementations for few-shot prompts."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Iterator

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

try:
    from context_collectors.base import BaseContextCollector
    from utils.models import ContextFragment
    from utils.paths import discover_project_paths
    from utils.text import condense_whitespace, truncate
except ImportError:
    from AutoGenChecker.context_collectors.base import BaseContextCollector
    from AutoGenChecker.utils.models import ContextFragment
    from AutoGenChecker.utils.paths import discover_project_paths
    from AutoGenChecker.utils.text import condense_whitespace, truncate

try:  # Optional dependency.
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency guard
    yaml = None


class CheckerExampleCollector(BaseContextCollector):
    """Provide RELEVANT checker examples based on similarity matching.
    
    Smart similarity matching based on:
    1. Same input file types (e.g., both parse qor.rpt)
    2. Similar descriptions (semantic similarity)
    3. Same checker type (Type 1/2/3/4)
    4. Similar parsing patterns (regex, log parsing, etc.)
    
    This provides truly relevant few-shot examples that reduce development time.
    """

    name = "checker_examples"

    def __init__(
        self, 
        max_examples: int = 3, 
        max_script_chars: int = 1600,
        exclude_ai_generated: bool = False,  # Allow AI-generated examples by default
    ) -> None:
        self._max_examples = max_examples
        self._max_script_chars = max_script_chars
        self._exclude_ai_generated = exclude_ai_generated
        self._paths = discover_project_paths().ensure_exists()

    def collect(
        self, request=None
    ) -> Iterable[ContextFragment]:  # type: ignore[override]
        if not self._paths.check_modules_root:
            return []

        # Extract features from current request for similarity matching
        current_features = self._extract_request_features(request)
        
        # Collect all candidate examples with similarity scores
        candidates = []
        for example in self._iter_examples():
            # Skip AI-generated if configured
            if self._exclude_ai_generated and self._is_ai_generated(example['script_text']):
                continue
            
            # Calculate similarity score
            score = self._calculate_similarity(current_features, example)
            candidates.append((score, example))
        
        # Sort by similarity score (highest first) and take top N
        candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = candidates[:self._max_examples]
        
        # Build fragments from top matches
        fragments = []
        for score, example in top_candidates:
            fragment = self._build_fragment(example, similarity_score=score)
            fragments.append(fragment)
        
        return fragments
    
    def _extract_request_features(self, request) -> dict:
        """Extract features from request for similarity matching."""
        features = {
            'description': '',
            'input_files': [],
            'checker_type': None,
            'module': '',
        }
        
        if not request:
            return features
        
        # Extract from request object
        if hasattr(request, 'item_name'):
            features['description'] = request.item_name or ''
        if hasattr(request, 'target_files'):
            features['input_files'] = request.target_files or []
        if hasattr(request, 'module'):
            features['module'] = request.module or ''
        
        # Note: CheckerAgentRequest doesn't have requirements/waivers fields
        # Type detection would need to be done externally or from YAML metadata
        # For now, we'll skip type matching and rely on file/description similarity
        
        return features
    
    def _calculate_similarity(self, current_features: dict, example: dict) -> float:
        """Calculate similarity score between current task and example.
        
        Scoring (0-100):
        - Input file match: 40 points (most important - same parsing logic)
        - Checker type match: 30 points (same implementation pattern)
        - Description similarity: 20 points (similar purpose)
        - Same module: 10 points (bonus for context)
        """
        score = 0.0
        
        # 1. Input file similarity (40 points max)
        current_files = current_features.get('input_files', [])
        example_files = example['metadata'].get('input_files', []) if isinstance(example['metadata'], dict) else []
        
        if current_files and example_files:
            # Extract file extensions and base names
            current_types = set()
            for f in current_files:
                fname = Path(str(f)).name.lower()
                current_types.add(fname)
                # Also add extension
                if '.' in fname:
                    current_types.add(fname.split('.')[-1])
            
            example_types = set()
            for f in example_files:
                fname = Path(str(f)).name.lower()
                example_types.add(fname)
                if '.' in fname:
                    example_types.add(fname.split('.')[-1])
            
            # Exact filename match: full 40 points
            if current_types & example_types:
                overlap = len(current_types & example_types)
                score += min(40.0, overlap * 20.0)
        
        # 2. Checker type match (30 points)
        current_type = current_features.get('checker_type')
        example_type = self._detect_checker_type_from_metadata(example['metadata'])
        
        if current_type and example_type and current_type == example_type:
            score += 30.0
        
        # 3. Description similarity (20 points)
        current_desc = current_features.get('description', '').lower()
        example_desc = str(example['metadata'].get('item_desc', '')).lower() if isinstance(example['metadata'], dict) else ''
        
        if current_desc and example_desc:
            # Simple keyword matching
            current_keywords = set(current_desc.split())
            example_keywords = set(example_desc.split())
            common = current_keywords & example_keywords
            
            if common:
                similarity_ratio = len(common) / max(len(current_keywords), len(example_keywords))
                score += similarity_ratio * 20.0
        
        # 4. Same module bonus (10 points)
        if current_features.get('module') == example.get('module'):
            score += 10.0
        
        return score
    
    def _detect_checker_type_from_metadata(self, metadata: dict) -> int | None:
        """Detect checker type from YAML metadata."""
        if not isinstance(metadata, dict):
            return None
        
        req = metadata.get('requirements', {})
        if not isinstance(req, dict):
            return None
        
        req_value = req.get('value', 'N/A')
        pattern_items = req.get('pattern_items', [])
        
        waiver = metadata.get('waivers', {})
        waiver_value = waiver.get('value', 'N/A') if isinstance(waiver, dict) else 'N/A'
        
        # Type detection
        if req_value == 'N/A' and waiver_value in ['N/A', 0]:
            return 1
        elif req_value != 'N/A' and pattern_items and waiver_value in ['N/A', 0]:
            return 2
        elif req_value != 'N/A' and pattern_items and waiver_value not in ['N/A', 0]:
            return 3
        elif req_value == 'N/A' and waiver_value not in ['N/A', 0]:
            return 4
        
        return None

    def _iter_examples(self) -> Iterator[dict[str, object]]:
        root = self._paths.check_modules_root
        if not root:
            return

        for module_dir in sorted(root.iterdir()):
            if not module_dir.is_dir() or module_dir.name.lower() == "common":
                continue

            items_dir = module_dir / "inputs" / "items"
            scripts_dir = module_dir / "scripts" / "checker"
            if not items_dir.exists() or not scripts_dir.exists():
                continue

            for config_file in sorted(items_dir.glob("*.yaml")):
                item_id = config_file.stem
                script_path = scripts_dir / f"{item_id}.py"
                if not script_path.exists():
                    continue

                metadata = self._load_metadata(config_file)
                script_text = self._read_text(script_path)
                if not script_text.strip():
                    continue

                yield {
                    "module": module_dir.name,
                    "item_id": item_id,
                    "config_file": config_file,
                    "script_path": script_path,
                    "metadata": metadata,
                    "script_text": script_text,
                }

    def _load_metadata(self, config_file: Path) -> dict[str, object]:
        if yaml is None:
            return {}
        try:
            with config_file.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except Exception:
            return {}

    def _read_text(self, script_path: Path) -> str:
        try:
            return script_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return script_path.read_text(encoding="latin-1", errors="ignore")
    
    def _is_ai_generated(self, script_text: str) -> bool:
        """Check if script was generated by AutoGenChecker AI.
        
        Detection markers:
        - "Author: AutoGenChecker AI"
        - "Refactored: YYYY-MM-DD (Using checker_templates"
        """
        if "Author: AutoGenChecker AI" in script_text:
            return True
        
        if "Refactored:" in script_text and "(Using checker_templates" in script_text:
            return True
        
        return False

    def _build_fragment(
        self, 
        example: dict[str, object], 
        similarity_score: float = 0.0
    ) -> ContextFragment:
        metadata = example.get("metadata", {})
        script_text = str(example["script_text"])
        header_lines: list[str] = []

        # Show similarity score to help LLM understand relevance
        if similarity_score > 0:
            header_lines.append(f"Similarity Score: {similarity_score:.1f}/100 (higher = more relevant)")

        description = metadata.get("item_desc") if isinstance(metadata, dict) else None
        if description:
            header_lines.append(f"Description: {description}")

        input_files = []
        if isinstance(metadata, dict):
            raw_inputs = metadata.get("input_files")
            if isinstance(raw_inputs, list):
                input_files = [str(entry) for entry in raw_inputs]
            elif isinstance(raw_inputs, str):
                input_files = [raw_inputs]
        if input_files:
            # Extract just the filename for readability
            file_names = [Path(str(f)).name for f in input_files]
            header_lines.append("Input Files: " + ", ".join(file_names))

        # Show checker type if detected
        checker_type = self._detect_checker_type_from_metadata(metadata)
        if checker_type:
            header_lines.append(f"Checker Type: Type {checker_type}")

        body_lines = ["\n".join(header_lines), "Code:", truncate(script_text, max_chars=self._max_script_chars)]
        fragment_body = condense_whitespace("\n".join(line for line in body_lines if line))

        title = f"Similar example: {example['item_id']} from {example['module']}"
        source = str(example.get("script_path"))
        return ContextFragment(
            title=title,
            content=fragment_body,
            source=source,
            importance="high",
        )
