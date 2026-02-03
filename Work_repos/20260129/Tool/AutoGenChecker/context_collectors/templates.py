"""Context collector for checker templates."""

from __future__ import annotations

import re
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
except ImportError:
    from AutoGenChecker.context_collectors.base import BaseContextCollector
    from AutoGenChecker.utils.models import CheckerAgentRequest, ContextFragment
    from AutoGenChecker.utils.paths import discover_project_paths


class TemplateCollector(BaseContextCollector):
    """
    Collector for BaseChecker and checker_templates.
    
    According to Development_prompt.md:
    "PRIORITY: Check common.checker_templates first.
     Use existing templates whenever possible to reduce code duplication."
    
    This collector helps LLM choose the right template.
    """
    
    name = "templates"
    
    def __init__(self):
        self._paths = discover_project_paths().ensure_exists()
    
    def collect(
        self, request: CheckerAgentRequest | None = None
    ) -> Iterable[ContextFragment]:
        """
        Collect available template information.
        
        Returns:
        1. Available templates in common/checker_templates/
        2. BaseChecker usage guide
        """
        fragments: list[ContextFragment] = []
        
        if not self._paths.check_modules_root:
            return fragments
        
        # Check for checker_templates directory
        templates_dir = self._paths.check_modules_root / "common" / "checker_templates"
        
        if templates_dir.exists() and templates_dir.is_dir():
            template_fragments = self._collect_templates(templates_dir)
            fragments.extend(template_fragments)
        
        # Always include BaseChecker reference
        base_checker_fragment = self._collect_base_checker_guide()
        if base_checker_fragment:
            fragments.append(base_checker_fragment)
        
        return fragments
    
    def _collect_templates(self, templates_dir: Path) -> list[ContextFragment]:
        """Collect information about available templates."""
        fragments = []
        
        template_files = list(templates_dir.glob("*.py"))
        template_files = [f for f in template_files if f.name != "__init__.py"]
        
        if not template_files:
            return fragments
        
        # Create summary fragment
        summary_lines = [
            "AVAILABLE CHECKER TEMPLATES",
            "=" * 70,
            "",
            "⭐ PRIORITY: Use these templates if applicable!",
            "They reduce code duplication and provide standardized patterns.",
            "",
        ]
        
        for template_file in sorted(template_files):
            template_name = template_file.stem
            docstring = self._extract_docstring(template_file)
            
            summary_lines.append(f"📄 {template_name}")
            if docstring:
                # Extract first line of docstring
                first_line = docstring.split('\n')[0].strip()
                summary_lines.append(f"   {first_line}")
            summary_lines.append(f"   Path: {template_file}")
            summary_lines.append("")
        
        summary_lines.extend([
            "USAGE:",
            "  from checker_templates import TemplateName",
            "  class MyChecker(TemplateName):",
            "      # Override specific methods as needed",
            "",
            "=" * 70,
        ])
        
        fragments.append(ContextFragment(
            title="Available Checker Templates (PRIORITY)",
            content="\n".join(summary_lines),
            source=str(templates_dir),
            importance="high"
        ))
        
        return fragments
    
    def _collect_base_checker_guide(self) -> ContextFragment | None:
        """Collect BaseChecker usage guide."""
        if not self._paths.check_modules_root:
            return None
        
        base_checker_file = self._paths.check_modules_root / "common" / "base_checker.py"
        
        if not base_checker_file.exists():
            return None
        
        # Extract key information from BaseChecker
        content = self._create_base_checker_guide(base_checker_file)
        
        return ContextFragment(
            title="BaseChecker Framework",
            content=content,
            source=str(base_checker_file),
            importance="medium"
        )
    
    def _extract_docstring(self, file_path: Path) -> str:
        """Extract module docstring from Python file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Find first docstring (triple quotes)
            match = re.search(
                r'^\s*["\']{{3}}(.*?)["\']{{3}}',
                content,
                re.MULTILINE | re.DOTALL
            )
            
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        
        return ""
    
    def _create_base_checker_guide(self, base_checker_file: Path) -> str:
        """Create a concise BaseChecker usage guide."""
        lines = [
            "BASECHECKER FRAMEWORK",
            "=" * 70,
            "",
            "When templates don't fit, inherit from BaseChecker directly.",
            "",
            "Required imports:",
            "  from base_checker import BaseChecker, CheckResult",
            "  from output_formatter import DetailItem, Severity, create_check_result",
            "",
            "Class structure:",
            "  class MyChecker(BaseChecker):",
            "      def __init__(self):",
            "          super().__init__(",
            "              check_module=\"MODULE_NAME\",",
            "              item_id=\"ITEM_ID\",",
            "              item_desc=\"DESCRIPTION\"",
            "          )",
            "",
            "      def execute_check(self) -> CheckResult:",
            "          # 1. Detect type",
            "          checker_type = self.detect_checker_type()",
            "",
            "          # 2. Parse files",
            "          parsed_data = self._parse_files()",
            "",
            "          # 3. Execute based on type",
            "          if checker_type == 1:",
            "              return self._execute_type1(parsed_data)",
            "          elif checker_type == 2:",
            "              return self._execute_type2(parsed_data)",
            "          elif checker_type == 3:",
            "              return self._execute_type3(parsed_data)",
            "          else:",
            "              return self._execute_type4(parsed_data)",
            "",
            "      def _parse_files(self) -> dict:",
            "          # Implement file parsing based on Step 2.5 analysis",
            "          pass",
            "",
            "      def _execute_type1/2/3/4(self, parsed_data: dict) -> CheckResult:",
            "          # Implement type-specific logic",
            "          pass",
            "",
            "Key methods available:",
            "  - self.detect_checker_type() -> int  # Auto-detect Type 1/2/3/4",
            "  - self.get_requirements() -> dict    # Get requirements config",
            "  - self.get_waivers() -> dict         # Get waivers config",
            "  - self.logger                        # Logger instance",
            "  - self.root                          # Workspace root Path",
            "  - self.input_base                    # Module inputs/ directory",
            "",
            "Return value:",
            "  Use create_check_result() to create CheckResult:",
            "    return create_check_result(",
            "        value=...,              # Numeric value or 'N/A'",
            "        is_pass=True/False,     # Overall status",
            "        has_pattern_items=...,  # Whether pattern_items used",
            "        has_waiver_value=...,   # Whether waivers used",
            "        details=[...],          # List of DetailItem",
            "        info_groups={...},      # Optional: dict of info groups",
            "        error_groups={...},     # Optional: dict of error groups",
            "        item_desc=self.item_desc",
            "    )",
            "",
            "=" * 70,
        ]
        
        return "\n".join(lines)
