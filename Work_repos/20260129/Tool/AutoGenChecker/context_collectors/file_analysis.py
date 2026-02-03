"""Context collector for input file analysis (Step 2.5)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional

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


class FileAnalysisCollector(BaseContextCollector):
    """
    Collector for Step 2.5: Analyze actual input files.
    
    This is CRITICAL according to DEVELOPER_WORKFLOW_DIAGRAM.md:
    - Must analyze real file formats
    - Do NOT guess patterns
    - Extract actual data samples
    
    Priority: CRITICAL (highest importance)
    """
    
    name = "file_analysis"
    
    def __init__(self):
        self._paths = discover_project_paths().ensure_exists()
    
    def collect(
        self, request: CheckerAgentRequest | None = None
    ) -> Iterable[ContextFragment]:
        """
        Analyze input files and return detailed analysis results.
        
        Returns fragments containing:
        - File type identification
        - Detected patterns with regex
        - Real data samples
        - Parsing strategy recommendations
        - Output format suggestions (info_groups/details)
        """
        if request is None or not request.target_files:
            return []
        
        # Import FileFormatAnalyzer
        try:
            from AutoGenChecker.file_format_analyzer import FileFormatAnalyzer
            analyzer = FileFormatAnalyzer()
        except ImportError:
            return []
        
        fragments: list[ContextFragment] = []
        
        for file_path_str in request.target_files:
            # Locate the file
            located_path = self._locate_file(file_path_str, request.module)
            
            if not located_path or not located_path.exists():
                # File not found - create warning fragment
                fragments.append(ContextFragment(
                    title=f"⚠️ File Not Found: {Path(file_path_str).name}",
                    content=f"Input file '{file_path_str}' could not be located.\n"
                           f"Generic template will be generated.\n"
                           f"Recommendation: Place file in module inputs/ directory for analysis.",
                    source=file_path_str,
                    importance="critical"
                ))
                continue
            
            # Analyze the file
            try:
                analysis = analyzer.analyze_file_detailed(str(located_path))
                
                # Format analysis as context fragment
                content = self._format_analysis(analysis)
                
                fragments.append(ContextFragment(
                    title=f"📊 File Analysis: {analysis.get('file_name', 'Unknown')}",
                    content=content,
                    source=str(located_path),
                    importance="critical"  # Highest priority
                ))
            except Exception as e:
                fragments.append(ContextFragment(
                    title=f"⚠️ Analysis Failed: {located_path.name}",
                    content=f"Failed to analyze file: {e}\n"
                           f"Generic template will be used.",
                    source=str(located_path),
                    importance="medium"
                ))
        
        return fragments
    
    def _locate_file(self, file_path_str: str, module: str) -> Optional[Path]:
        """Try to locate input file in various locations."""
        file_path = Path(file_path_str)
        
        # If absolute and exists
        if file_path.is_absolute() and file_path.exists():
            return file_path
        
        # Try relative to module inputs/
        if not self._paths.check_modules_root:
            return None
        
        module_dir = self._paths.check_modules_root / module
        locations = [
            module_dir / "inputs" / file_path,
            module_dir / file_path,
            self._paths.workspace_root / "IP_project_folder" / file_path,
            self._paths.workspace_root / file_path,
        ]
        
        for loc in locations:
            if loc.exists():
                return loc
        
        return None
    
    def _format_analysis(self, analysis: dict) -> str:
        """
        Format file analysis results for LLM consumption with enhanced intelligence.
        
        Creates structured text that emphasizes:
        1. File type and format
        2. Detected patterns with examples
        3. Parsing strategy with code hints
        4. Output format recommendations
        5. Data structure hints (for Dict metadata)
        6. Common pitfalls and solutions
        """
        lines = [
            "=" * 70,
            f"FILE TYPE: {analysis.get('file_type', 'Unknown').upper()}",
            "=" * 70,
            "",
            "📁 File Information:",
            f"  Name: {analysis.get('file_name', 'Unknown')}",
            f"  Path: {analysis.get('file_path', 'N/A')}",
            f"  Size: {analysis.get('file_size', 0):,} bytes",
            f"  Lines: {analysis.get('total_lines', 0):,}",
            f"  Non-empty: {analysis.get('non_empty_lines', 0):,}",
            f"  Encoding: {analysis.get('encoding', 'utf-8')}",
            "",
        ]
        
        # Add file structure hint
        structure_hint = self._detect_structure_type(analysis)
        if structure_hint:
            lines.extend([
                "🏗️ DETECTED STRUCTURE:",
                f"  {structure_hint}",
                ""
            ])
        
        # Patterns section
        patterns = analysis.get('patterns', [])
        if patterns:
            lines.extend([
                "🔍 DETECTED PATTERNS (use these exact patterns):",
                ""
            ])
            for idx, pattern in enumerate(patterns[:10], 1):
                lines.append(f"  [{idx}] Pattern: {pattern.get('name', 'Unknown')}")
                lines.append(f"      Regex: {pattern.get('regex', 'N/A')}")
                lines.append(f"      Example: {pattern.get('example', 'N/A')}")
                lines.append(f"      Count: {pattern.get('count', 0)}")
                lines.append("")
        else:
            lines.extend([
                "🔍 No specific patterns detected.",
                "   Use generic line-by-line parsing.",
                ""
            ])
        
        # Parsing strategy
        strategy = analysis.get('parsing_strategy', '')
        if strategy:
            lines.extend([
                "⚙️ RECOMMENDED PARSING STRATEGY:",
                f"  {strategy}",
                ""
            ])
        
        # Output recommendations
        output_suggestion = analysis.get('output_suggestion', {})
        if output_suggestion:
            lines.extend([
                "📤 OUTPUT FORMAT RECOMMENDATIONS:",
                f"  INFO01 should display: {output_suggestion.get('info01', 'N/A')}",
                f"  ERROR01 should display: {output_suggestion.get('error01', 'N/A')}",
                "",
                "⚠️ CRITICAL: info_groups.items MUST match details.name",
                ""
            ])
        
        # Real data sample
        sample_data = analysis.get('sample_data', '')
        if sample_data:
            lines.extend([
                "📝 REAL DATA SAMPLE (first 500 chars):",
                "-" * 70,
            ])
            for line in sample_data[:500].split('\n')[:15]:
                lines.append(f"  {line}")
            lines.extend([
                "-" * 70,
                ""
            ])
        
        # Keywords if available
        keywords = analysis.get('keywords', {})
        if keywords:
            lines.extend([
                "🔑 KEY WORDS (for validation):",
            ])
            for word, count in list(keywords.items())[:10]:
                lines.append(f"  - {word}: {count} occurrences")
            lines.append("")
        
        # Add template recommendations based on analysis
        template_hints = self._generate_template_hints(analysis)
        if template_hints:
            lines.extend([
                "💡 TEMPLATE USAGE HINTS:",
                ""
            ])
            for hint in template_hints:
                lines.append(f"  • {hint}")
            lines.append("")
        
        # Add common pitfalls
        pitfalls = self._detect_common_pitfalls(analysis)
        if pitfalls:
            lines.extend([
                "⚠️ COMMON PITFALLS TO AVOID:",
                ""
            ])
            for pitfall in pitfalls:
                lines.append(f"  ❌ {pitfall}")
            lines.append("")
        
        lines.extend([
            "=" * 70,
            "⚠️ CRITICAL REMINDERS:",
            "  1. Use the EXACT patterns detected above - do NOT guess!",
            "  2. Preserve metadata (line_number, file_path) in Dict format",
            "  3. Set extra_severity=Severity.FAIL for violations",
            "  4. Test with actual file before submitting",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def _detect_structure_type(self, analysis: dict) -> str:
        """Detect file structure type for better parsing hints."""
        file_type = analysis.get('file_type', '').lower()
        patterns = analysis.get('patterns', [])
        
        # Detect structured formats
        if file_type == 'report':
            if any('section' in p.get('name', '').lower() for p in patterns):
                return "Section-based report (use section extraction template)"
            if any('table' in p.get('name', '').lower() for p in patterns):
                return "Tabular report (use row-by-row parsing)"
            return "Free-form report (use pattern matching)"
        
        if file_type == 'log':
            if any('timestamp' in p.get('name', '').lower() for p in patterns):
                return "Timestamped log (filter by time if needed)"
            return "Sequential log (use line-by-line parsing)"
        
        if file_type in ['tcl', 'script']:
            if any('command' in p.get('name', '').lower() for p in patterns):
                return "Command script (extract commands with args)"
            return "Script file (parse statements)"
        
        return ""
    
    def _generate_template_hints(self, analysis: dict) -> list[str]:
        """Generate template usage hints based on file analysis."""
        hints = []
        patterns = analysis.get('patterns', [])
        file_type = analysis.get('file_type', '')
        
        # Hint 1: Dict vs List
        if analysis.get('total_lines', 0) > 0:
            hints.append(
                "Use Dict format for items: "
                "{\"item\": {\"line_number\": N, \"file_path\": path}}"
            )
        
        # Hint 2: Metadata extraction
        if patterns:
            hints.append(
                f"Extract metadata from {len(patterns)} detected pattern(s) "
                "to preserve source location"
            )
        
        # Hint 3: Output format
        if file_type in ['report', 'log']:
            hints.append(
                "Use build_complete_output() with found_items and missing_items"
            )
        
        # Hint 4: Severity
        violation_patterns = [p for p in patterns if 'error' in p.get('name', '').lower() 
                            or 'fail' in p.get('name', '').lower()
                            or 'violation' in p.get('name', '').lower()]
        if violation_patterns:
            hints.append(
                "Violations detected - set extra_severity=Severity.FAIL for failures"
            )
        
        # Hint 5: Pattern matching
        if len(patterns) > 3:
            hints.append(
                f"Multiple patterns ({len(patterns)}) - consider pattern dictionary "
                "for efficient matching"
            )
        
        return hints
    
    def _detect_common_pitfalls(self, analysis: dict) -> list[str]:
        """Detect potential pitfalls based on file analysis."""
        pitfalls = []
        patterns = analysis.get('patterns', [])
        
        # Pitfall 1: Missing file
        if not analysis.get('exists', False):
            pitfalls.append(
                "File not found - ensure file path is correct in YAML config"
            )
        
        # Pitfall 2: Empty file
        if analysis.get('total_lines', 0) == 0:
            pitfalls.append(
                "File is empty - handle empty file case in code"
            )
        
        # Pitfall 3: No clear patterns
        if not patterns:
            pitfalls.append(
                "No clear patterns detected - may need manual pattern definition"
            )
        
        # Pitfall 4: Complex patterns
        complex_patterns = [p for p in patterns if len(p.get('regex', '')) > 100]
        if complex_patterns:
            pitfalls.append(
                "Complex regex detected - test thoroughly with edge cases"
            )
        
        # Pitfall 5: Ambiguous groups
        if len(patterns) > 10:
            pitfalls.append(
                "Many patterns detected - ensure info_groups.items match details.name"
            )
        
        return pitfalls
