"""
File analysis functionality for IntelligentCheckerAgent.

Handles AI-powered analysis of input files to understand format and patterns.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING
import re
import json
import glob

if TYPE_CHECKING:
    pass


class FileAnalysisMixin:
    """Mixin for file analysis functionality."""
    
    def _ai_analyze_input_files(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Use AI to analyze actual input files.
        
        This implements Step 2.5 from DEVELOPER_TASK_PROMPTS.md:
        - Read actual file content
        - Identify file format & structure
        - Extract key patterns with regex
        - Record real data samples
        - Define output format (INFO01, ERROR01)
        """
        print("\n" + "─"*80)
        print("[Step 2/9] 🔍 Analyzing Input Files")
        print("─"*80)
        
        input_files = config.get('input_files', [])
        
        if not input_files:
            self._log("No input files specified in config", "WARNING", "⚠️")
            return {}
        
        analysis_results = {}
        
        for file_path in input_files:
            self._log(f"Analyzing: {Path(file_path).name}", "INFO", "📁")
            
            # Expand environment variables like ${CHECKLIST_ROOT}
            expanded_path = self._expand_path_variables(file_path)
            
            # Check if path contains wildcards
            if '*' in expanded_path or '?' in expanded_path:
                # Try to find matching files
                matching_files = list(glob.glob(expanded_path))
                
                # If no matches found, try relative to project root
                if not matching_files:
                    try:
                        from utils.paths import discover_project_paths
                    except ImportError:
                        from AutoGenChecker.utils.paths import discover_project_paths
                    
                    paths = discover_project_paths()
                    relative_expanded = str(paths.workspace_root / expanded_path)
                    matching_files = list(glob.glob(relative_expanded))
                
                if matching_files:
                    # Use first matching file for analysis
                    file_obj = Path(matching_files[0])
                    if self.verbose:
                        print(f"    💡 Found {len(matching_files)} matching file(s), analyzing first: {file_obj.name}")
                else:
                    if self.verbose:
                        print(f"    ⚠️  No files match pattern: {file_path}")
                    analysis_results[str(file_path)] = {
                        'exists': False,
                        'file_type': 'pattern',
                        'note': 'Wildcard pattern - will be resolved at runtime',
                    }
                    continue
            else:
                # No wildcards - normal file path
                file_obj = Path(expanded_path)
                if not file_obj.exists():
                    # Try relative to project root
                    try:
                        from utils.paths import discover_project_paths
                    except ImportError:
                        from AutoGenChecker.utils.paths import discover_project_paths
                    
                    paths = discover_project_paths()
                    file_obj = paths.workspace_root / expanded_path
            
            if file_obj.exists():
                # First, find similar examples that parse the same file type
                similar_examples = self._find_similar_file_parsing_examples(file_path)
                
                # Call AI to analyze file (with similar examples as reference)
                analysis = self._call_ai_for_file_analysis(file_obj, config, similar_examples)
                analysis_results[str(file_path)] = analysis
                
                if self.verbose:
                    print(f"   ✅ Analysis completed")
                    print(f"      Format: {analysis.get('file_type', 'unknown')}")
                    print(f"      Patterns: {len(analysis.get('patterns', []))}")
                    if similar_examples:
                        print(f"      📚 Referenced {len(similar_examples)} similar parsing example(s)")
            else:
                if self.verbose:
                    print(f"    ⚠️  File not found: {file_path}")
                analysis_results[str(file_path)] = {
                    'exists': False,
                    'file_type': 'unknown',
                }
        
        return analysis_results
    
    def _find_similar_file_parsing_examples(self, target_file_path: str) -> list[dict[str, Any]]:
        """
        Find existing checkers that parse the same/similar input file.
        
        Returns parsing examples with:
        - item_id: Checker ID
        - description: What it checks
        - parsing_snippet: Code snippet showing how it parses the file
        - patterns: Regex patterns used
        """
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        if not paths.check_modules_root:
            return []
        
        # Extract target filename
        target_filename = Path(target_file_path).name.lower()
        
        examples = []
        
        # Search all checker scripts and configs
        for module_dir in paths.check_modules_root.iterdir():
            if not module_dir.is_dir() or module_dir.name.lower() == "common":
                continue
            
            items_dir = module_dir / "inputs" / "items"
            scripts_dir = module_dir / "scripts" / "checker"
            
            if not items_dir.exists() or not scripts_dir.exists():
                continue
            
            for config_file in items_dir.glob("*.yaml"):
                item_id = config_file.stem
                script_path = scripts_dir / f"{item_id}.py"
                
                if not script_path.exists():
                    continue
                
                # Load YAML to check input_files
                try:
                    import yaml
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    
                    if not config_data:
                        continue
                    
                    input_files = config_data.get('input_files', [])
                    if not input_files:
                        continue
                    
                    # Check if any input file matches target
                    has_match = False
                    for input_file in input_files:
                        input_filename = Path(str(input_file)).name.lower()
                        if input_filename == target_filename:
                            has_match = True
                            break
                    
                    if not has_match:
                        continue
                    
                    # Extract parsing logic from script
                    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                        script_content = f.read()
                    
                    # Extract _parse_input_files method
                    parsing_snippet = self._extract_parsing_method(script_content)
                    
                    # Extract regex patterns
                    patterns = re.findall(r'r["\'](.+?)["\']', script_content)
                    
                    examples.append({
                        'item_id': item_id,
                        'description': config_data.get('description', 'N/A'),
                        'parsing_snippet': parsing_snippet[:800] if parsing_snippet else 'N/A',
                        'patterns': patterns[:5],  # Top 5 patterns
                    })
                    
                    # Limit to 3 examples
                    if len(examples) >= 3:
                        break
                        
                except Exception:
                    continue
            
            if len(examples) >= 3:
                break
        
        return examples
    
    def _extract_parsing_method(self, script_content: str) -> str:
        """Extract _parse_input_files method from checker script."""
        # Try to find the method
        match = re.search(
            r'def _parse_input_files\(self\).*?(?=\n    def |\nclass |\Z)',
            script_content,
            re.DOTALL
        )
        
        if match:
            return match.group(0)
        
        return ""
    
    def _call_ai_for_file_analysis(
        self,
        file_path: Path,
        config: dict[str, Any],
        similar_examples: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Call LLM to analyze file format and extraction patterns.
        
        AI receives:
        - Actual file content (first 500 lines or 50KB)
        - Checker description
        - Task: Identify patterns, suggest parsing logic
        
        AI returns:
        - File type (log, report, timing, sdc, etc.)
        - Key patterns with regex
        - Real data samples
        - Recommended INFO/ERROR format
        """
        # Read file content (limit to 200 lines or 30KB to avoid timeout)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:200]  # First 200 lines max
                content = ''.join(lines)
                
                # Further limit by size (30KB max)
                max_bytes = 30 * 1024
                if len(content.encode('utf-8')) > max_bytes:
                    content = content[:max_bytes // 2]  # Rough char count
                    content += "\n\n... [File truncated for analysis] ..."
                    
        except Exception as e:
            return {
                'exists': True,
                'file_type': 'unreadable',
                'error': str(e),
            }
        
        # Build AI prompt
        prompt = self._build_file_analysis_prompt(
            file_path.name,
            content,
            config['description'],
            similar_examples,
        )
        
        # Call LLM (use cached agent)
        agent = self._get_llm_agent()
        
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        llm_config = LLMCallConfig(temperature=0.1)  # Low temp for analysis
        
        # Add exception handling for LLM call
        try:
            self._log(f"   Calling LLM to analyze {file_path.name}...", "INFO")
            response = agent._llm_client.complete(prompt, config=llm_config)
            # Don't log completion here - will be shown in summary below
        except Exception as e:
            self._log(f"LLM call failed for {file_path.name}: {str(e)}", "ERROR", "❌")
            self._log(f"Exception type: {type(e).__name__}", "ERROR")
            self._log(f"Exception details: {repr(e)}", "ERROR")
            # Return fallback analysis
            return {
                'exists': True,
                'file_type': 'error_analyzing',
                'error': str(e),
                'note': 'LLM analysis failed - using fallback',
                'patterns': [],
            }
        
        # Parse AI response to extract structured analysis
        analysis = self._parse_ai_file_analysis(response.text)
        analysis['exists'] = True
        
        return analysis
    
    def _build_file_analysis_prompt(
        self,
        filename: str,
        content: str,
        description: str,
        similar_examples: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build prompt for AI file analysis with similar parsing examples."""
        
        # Build examples section if available
        examples_section = ""
        if similar_examples:
            examples_section = "\n\n" + "="*80 + "\n"
            examples_section += "📚 SIMILAR FILE PARSING EXAMPLES (Reference for parsing logic)\n"
            examples_section += "="*80 + "\n\n"
            
            for i, example in enumerate(similar_examples, 1):
                examples_section += f"Example {i}: {example['item_id']}\n"
                examples_section += f"Description: {example['description']}\n"
                
                if example['patterns']:
                    examples_section += f"Patterns used:\n"
                    for pattern in example['patterns'][:3]:
                        examples_section += f"  - r'{pattern}'\n"
                
                if example['parsing_snippet'] and example['parsing_snippet'] != 'N/A':
                    examples_section += f"\nParsing method excerpt:\n```python\n{example['parsing_snippet']}\n```\n"
                
                examples_section += "\n" + "-"*40 + "\n\n"
            
            examples_section += "Use these examples as reference for:\n"
            examples_section += "- Similar regex patterns that work for this file type\n"
            examples_section += "- Proven parsing strategies\n"
            examples_section += "- Common field extraction logic\n"
            examples_section += "="*80 + "\n"
        
        return f"""Analyze this input file for checker development (DEVELOPER_TASK_PROMPTS.md Phase 1).

Checker: {description}
File: {filename}
{examples_section}
File Content (first 500 lines):
```
{content[:10000]}  # Limit to 10KB
```

CRITICAL: Follow Phase 1 Analysis Steps from DEVELOPER_TASK_PROMPTS.md v1.1.0

Please analyze and provide:

1. **File Type**: (timing_report, sta_log, synthesis_log, sdc_file, spef_annotation, etc.)

2. **Define Output Format FIRST** (determines parsing granularity):
   - INFO01 should display: <what field/data? file paths? views? items? counts?>
   - ERROR01 should display: <what violations? net names? error codes?>
   - Display format: "[item_name] (view: view_name)" vs "error_code: message"
   - This determines what data must be extracted and associated during parsing

3. **Key Patterns** (3-5 most important, based on output requirements):
   For each pattern provide:
   - Pattern description
   - Regex or search string (actual regex, e.g. r'\\*\\*ERROR:\\s*\\(SPEF-(\\d+)\\)\\s*(.+)')
   - Example line from file
   - What data to extract: error codes, net names, view associations, line numbers
   - How it relates to INFO01/ERROR01 output format

4. **Parsing Strategy**:
   - Multi-file handling: aggregate vs per-file results
   - How to iterate through file (line-by-line, section-by-section, etc.)
   - What to look for (keywords, headers, delimiters)
   - Edge cases: empty files, missing sections, format variations

5. **Real Data Samples** (3-5 lines minimum):
   ```
   Sample Line 1: <paste actual content>
   Sample Line 2: <paste actual content>
   Sample Line 3: <paste actual content>
   Pattern: <actual regex>
   Extraction: <what gets captured>
   ```

6. **Template Recommendations**:
   - Can use parse_log_with_patterns()? (for regex-based parsing)
   - Can use normalize_command()? (for text normalization)
   - Other template helpers applicable?

Format your response as structured JSON for easy parsing."""
    
    def _parse_ai_file_analysis(self, ai_response: str) -> dict[str, Any]:
        """Parse AI's structured file analysis response."""
        # Look for JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Fallback: simple text parsing
        return {
            'file_type': 'analyzed',
            'patterns': [],
            'parsing_strategy': ai_response[:500],
            'ai_raw_response': ai_response,
        }
    
    def _expand_path_variables(self, path: str) -> str:
        """Expand environment variables in path."""
        import os
        
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        
        # Replace ${CHECKLIST_ROOT} with actual path
        if '${CHECKLIST_ROOT}' in path:
            path = path.replace('${CHECKLIST_ROOT}', str(paths.workspace_root))
        
        # Replace ${IP_PROJECT_FOLDER} with actual path
        if '${IP_PROJECT_FOLDER}' in path:
            ip_folder = paths.workspace_root / "IP_project_folder"
            path = path.replace('${IP_PROJECT_FOLDER}', str(ip_folder))
        
        # Replace ${WORK} with actual path
        if '${WORK}' in path:
            work_folder = paths.workspace_root / "Work"
            path = path.replace('${WORK}', str(work_folder))
        
        # Expand environment variables
        path = os.path.expandvars(path)
        
        return path
