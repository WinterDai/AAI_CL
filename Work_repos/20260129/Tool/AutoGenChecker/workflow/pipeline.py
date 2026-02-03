"""Core pipeline implementing the DEVELOPER_WORKFLOW_DIAGRAM.md steps."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

# Try relative import first, fall back to AutoGenChecker prefix
try:
    import sys
    _parent_dir = Path(__file__).parent.parent
    if str(_parent_dir) not in sys.path:
        sys.path.insert(0, str(_parent_dir))
    from utils.paths import discover_project_paths
except ImportError:
    from AutoGenChecker.utils.paths import discover_project_paths

from .models import CheckerArtifacts, WorkflowConfig


class CheckerGenerationPipeline:
    """
    Implements the 5-step workflow from DEVELOPER_WORKFLOW_DIAGRAM.md
    
    Steps:
    1. Update Configuration (Step 1)
    2. Generate README (Step 2)
    3. Analyze Input Files (Step 2.5) ⭐ MANDATORY
    4. Generate Code (Step 3)
    5. Setup Test (Step 4)
    """
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.context: dict[str, Any] = {}
        self.paths = discover_project_paths()
        self.start_time = time.time()
        
    def run_full_workflow(self) -> CheckerArtifacts:
        """Execute all workflow steps in sequence."""
        
        print(f"\n{'='*80}")
        print(f"🚀 Starting Checker Generation Workflow")
        print(f"{'='*80}")
        print(f"Module: {self.config.module}")
        print(f"Item ID: {self.config.item_id}")
        print(f"{'='*80}\n")
        
        artifacts = CheckerArtifacts(config={})
        
        # Step 1: Update Configuration
        print("[Step 1/5] Updating configuration...")
        config_data = self.step1_update_config()
        artifacts.config = config_data
        artifacts.workflow_steps_completed.append("config_update")
        print("✅ Configuration updated\n")
        
        # Step 2: Generate README
        if not self.config.skip_readme:
            print("[Step 2/5] Generating README documentation...")
            readme_content = self.step2_generate_readme(config_data)
            artifacts.readme = readme_content
            artifacts.workflow_steps_completed.append("readme_generation")
            print("✅ README generated\n")
        else:
            print("[Step 2/5] ⏭️  Skipped (--skip-readme)\n")
        
        # Step 2.5: Analyze Input Files (MANDATORY)
        print("[Step 2.5/5] 🔍 Analyzing input files (MANDATORY)...")
        file_analysis = self.step2_5_analyze_files(config_data)
        artifacts.file_analysis = file_analysis
        artifacts.workflow_steps_completed.append("file_analysis")
        
        if file_analysis:
            print(f"✅ Analyzed {len(file_analysis)} input file(s)")
            for idx, analysis in enumerate(file_analysis, 1):
                print(f"   {idx}. {analysis.get('file_name', 'Unknown')}: "
                      f"{analysis.get('file_type', 'Unknown type')}")
        else:
            print("⚠️  No input files found - will generate generic template")
        print()
        
        # Step 3: Generate Code
        print("[Step 3/5] 💻 Generating checker code...")
        code_content = self.step3_generate_code(
            config_data,
            artifacts.readme,
            file_analysis
        )
        artifacts.code = code_content
        artifacts.workflow_steps_completed.append("code_generation")
        print("✅ Code generated\n")
        
        # Step 4: Setup Test
        if not self.config.skip_test_setup:
            print("[Step 4/5] 🧪 Setting up test scaffolding...")
            test_artifacts = self.step4_setup_test(config_data, code_content)
            artifacts.test_artifacts = test_artifacts
            artifacts.workflow_steps_completed.append("test_setup")
            print("✅ Test scaffolding created\n")
        else:
            print("[Step 4/5] ⏭️  Skipped (--skip-test-setup)\n")
        
        # Finalize
        artifacts.time_taken_seconds = time.time() - self.start_time
        artifacts.manual_refinement_needed = self._identify_manual_work(artifacts)
        
        self._print_summary(artifacts)
        
        return artifacts
    
    def step1_update_config(self) -> dict[str, Any]:
        """
        Step 1: Load and optionally update configuration
        
        Returns:
            Updated configuration dict
        """
        module_dir = self.paths.check_modules_root / self.config.module
        config_file = module_dir / "inputs" / "items" / f"{self.config.item_id}.yaml"
        
        if not config_file.exists():
            print(f"⚠️  Config file not found: {config_file}")
            print("   Creating minimal configuration...")
            config_data = {
                'item_id': self.config.item_id,
                'item_desc': self.config.item_desc or 'TBD',
                'input_files': self.config.input_files or [],
                'requirements': {'value': 'N/A', 'pattern_items': []},
                'waivers': {'value': 'N/A', 'waive_items': []},
            }
        else:
            if yaml is None:
                raise ImportError("PyYAML is required. Install with: pip install pyyaml")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Update config with CLI overrides
        if self.config.item_desc:
            config_data['item_desc'] = self.config.item_desc
        if self.config.input_files:
            config_data['input_files'] = self.config.input_files
        
        # Store in context
        self.context['config'] = config_data
        self.context['config_file'] = config_file
        
        return config_data
    
    def step2_generate_readme(self, config: dict[str, Any]) -> str:
        """
        Step 2: Generate README documentation
        
        Uses DEVELOPER_TASK_PROMPTS.md Step 2 template
        """
        try:
            from generate_readme import build_readme_prompt
        except ImportError:
            from AutoGenChecker.generate_readme import build_readme_prompt
        
        item_id = config.get('item_id', self.config.item_id)
        item_desc = config.get('item_desc', self.config.item_desc or 'TBD')
        input_files = config.get('input_files', [])
        
        if self.config.use_llm:
            # Use LLM to generate README
            prompt = build_readme_prompt(
                self.config.module,
                item_id,
                item_desc,
                input_files
            )
            
            # TODO: Call LLM here
            # For now, return a template
            readme_content = self._generate_readme_template(config)
        else:
            readme_content = self._generate_readme_template(config)
        
        # Store in context
        self.context['readme'] = readme_content
        
        return readme_content
    
    def step2_5_analyze_files(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Step 2.5: Analyze input files (MANDATORY)
        
        This step is CRITICAL according to DEVELOPER_WORKFLOW_DIAGRAM.md:
        - Must analyze actual file formats
        - Do NOT guess patterns
        - Extract real data samples
        
        Returns:
            List of file analysis results
        """
        try:
            from file_format_analyzer import FileFormatAnalyzer
        except ImportError:
            from AutoGenChecker.file_format_analyzer import FileFormatAnalyzer
        
        input_files = config.get('input_files', [])
        if isinstance(input_files, str):
            input_files = [input_files]
        
        analysis_results = []
        analyzer = FileFormatAnalyzer()
        
        for file_path_str in input_files:
            # Try to locate the file
            located_path = self._locate_input_file(file_path_str)
            
            if located_path and located_path.exists():
                try:
                    analysis = analyzer.analyze_file_detailed(str(located_path))
                    analysis_results.append(analysis)
                    print(f"   📄 Analyzed: {located_path.name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to analyze {located_path.name}: {e}")
            else:
                print(f"   ⚠️  File not found: {file_path_str}")
                # Create placeholder analysis
                analysis_results.append({
                    'file_name': Path(file_path_str).name,
                    'file_path': file_path_str,
                    'file_type': 'unknown',
                    'exists': False,
                    'patterns': [],
                    'sample_data': '',
                    'parsing_strategy': 'File not found - generic template will be used',
                })
        
        # Store in context
        self.context['file_analysis'] = analysis_results
        
        return analysis_results
    
    def step3_generate_code(
        self,
        config: dict[str, Any],
        readme: Optional[str],
        file_analysis: list[dict[str, Any]]
    ) -> str:
        """
        Step 3: Generate checker code
        
        MUST use file_analysis from Step 2.5
        """
        # Import here to avoid circular dependency
        try:
            from llm_checker_agent import build_agent_from_provider
            from context_collectors import TaskSpecCollector, CheckerExampleCollector
            from utils.models import CheckerAgentRequest
        except ImportError:
            from AutoGenChecker.llm_checker_agent import build_agent_from_provider
            from AutoGenChecker.context_collectors import TaskSpecCollector, CheckerExampleCollector
            from AutoGenChecker.utils.models import CheckerAgentRequest
        
        # Build request
        request = CheckerAgentRequest(
            module=self.config.module,
            item_id=self.config.item_id,
            item_name=config.get('item_desc', ''),
            target_files=config.get('input_files', []),
        )
        
        if self.config.use_llm:
            # Use LLM agent
            agent = build_agent_from_provider(
                self.config.llm_provider,
                default_model=self.config.llm_model,
            )
            
            # Collect context
            collectors = [
                TaskSpecCollector(),
                CheckerExampleCollector(max_examples=2),
            ]
            
            # Add file analysis to request notes
            if file_analysis:
                analysis_summary = self._format_file_analysis_for_prompt(file_analysis)
                request.notes = f"File Analysis Results:\n{analysis_summary}"
            
            # Generate code
            try:
                from utils.models import LLMCallConfig
            except ImportError:
                from AutoGenChecker.utils.models import LLMCallConfig
            config_obj = LLMCallConfig(temperature=self.config.temperature)
            
            result = agent.generate_checker(request, config=config_obj)
            code_content = result.checker_code
        else:
            # Generate template code
            code_content = self._generate_code_template(config, file_analysis)
        
        # Store in context
        self.context['code'] = code_content
        
        return code_content
    
    def step4_setup_test(
        self,
        config: dict[str, Any],
        code: str
    ) -> dict[str, Any]:
        """
        Step 4: Setup test scaffolding
        
        Creates:
        - Test data directories
        - Sample test script
        - Regression test entry
        """
        test_artifacts = {
            'test_data_created': False,
            'test_script_created': False,
            'regression_entry_created': False,
        }
        
        # For now, just return placeholder
        # TODO: Implement actual test scaffolding
        
        return test_artifacts
    
    def _locate_input_file(self, file_path_str: str) -> Optional[Path]:
        """Try to locate input file in various locations."""
        file_path = Path(file_path_str)
        
        # If absolute and exists
        if file_path.is_absolute() and file_path.exists():
            return file_path
        
        # Try relative to module inputs/
        module_dir = self.paths.check_modules_root / self.config.module
        locations = [
            module_dir / "inputs" / file_path,
            module_dir / file_path,
            self.paths.workspace_root / "IP_project_folder" / file_path,
            self.paths.workspace_root / file_path,
        ]
        
        for loc in locations:
            if loc.exists():
                return loc
        
        return None
    
    def _format_file_analysis_for_prompt(self, analysis_list: list[dict]) -> str:
        """Format file analysis results for LLM prompt."""
        lines = []
        for idx, analysis in enumerate(analysis_list, 1):
            lines.append(f"\nFile {idx}: {analysis.get('file_name', 'Unknown')}")
            lines.append(f"  Type: {analysis.get('file_type', 'Unknown')}")
            
            patterns = analysis.get('patterns', [])
            if patterns:
                lines.append(f"  Patterns: {', '.join(patterns[:3])}")
            
            strategy = analysis.get('parsing_strategy', '')
            if strategy:
                lines.append(f"  Strategy: {strategy}")
            
            sample = analysis.get('sample_data', '')
            if sample:
                lines.append(f"  Sample:\n{sample[:200]}")
        
        return '\n'.join(lines)
    
    def _generate_readme_template(self, config: dict) -> str:
        """Generate basic README template."""
        return f"""# {self.config.item_id} - README

## Overview

**Category**: TBD

**Input Files**: {', '.join(config.get('input_files', []))}

**Description**: {config.get('item_desc', 'TBD')}

## Check Logic

### Input Parsing
TODO: Describe how to parse input files

### Detection Logic
TODO: Describe PASS/FAIL determination logic

## Configuration Examples

See DEVELOPER_TASK_PROMPTS.md for Type 1/2/3/4 examples.
"""
    
    def _generate_code_template(
        self,
        config: dict,
        file_analysis: list[dict]
    ) -> str:
        """Generate basic code template when LLM is not available."""
        from datetime import datetime
        
        template = f'''"""
Checker ID: {self.config.item_id}
Description: {config.get('item_desc', 'TBD')}
Module: {self.config.module}

Author: AutoGenChecker
Date: {datetime.now().strftime('%Y-%m-%d')}
"""

from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult
from output_formatter import DetailItem, Severity, create_check_result


class Checker(BaseChecker):
    def __init__(self):
        super().__init__(
            check_module="{self.config.module}",
            item_id="{self.config.item_id}",
            item_desc="{config.get('item_desc', 'TBD')}"
        )
    
    def execute_check(self) -> CheckResult:
        """Execute the checker logic."""
        # TODO: Implement checker logic
        
        # Detect type
        checker_type = self.detect_checker_type()
        
        # Parse files
        parsed_data = self._parse_files()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1(parsed_data)
        elif checker_type == 2:
            return self._execute_type2(parsed_data)
        elif checker_type == 3:
            return self._execute_type3(parsed_data)
        else:
            return self._execute_type4(parsed_data)
    
    def _parse_files(self) -> dict:
        """Parse input files."""
        # TODO: Implement parsing logic based on file analysis
        return {{'items': []}}
    
    def _execute_type1(self, parsed_data: dict) -> CheckResult:
        """Type 1: Boolean check."""
        # TODO: Implement Type 1 logic
        return create_check_result(
            value="N/A",
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=[],
            item_desc=self.item_desc
        )
    
    def _execute_type2(self, parsed_data: dict) -> CheckResult:
        """Type 2: Value comparison."""
        # TODO: Implement Type 2 logic
        pass
    
    def _execute_type3(self, parsed_data: dict) -> CheckResult:
        """Type 3: Value with waivers."""
        # TODO: Implement Type 3 logic
        pass
    
    def _execute_type4(self, parsed_data: dict) -> CheckResult:
        """Type 4: Boolean with waivers."""
        # TODO: Implement Type 4 logic
        pass


if __name__ == '__main__':
    checker = Checker()
    checker.run()
'''
        return template
    
    def _identify_manual_work(self, artifacts: CheckerArtifacts) -> list[str]:
        """Identify what manual work is still needed."""
        manual_work = []
        
        if artifacts.code:
            if 'TODO' in artifacts.code:
                manual_work.append("Complete TODO sections in generated code")
            
            if not artifacts.file_analysis or not any(
                a.get('exists', False) for a in artifacts.file_analysis
            ):
                manual_work.append("Implement _parse_files() - no input files found")
        
        if artifacts.readme and 'TBD' in artifacts.readme:
            manual_work.append("Complete TBD sections in README")
        
        return manual_work
    
    def _print_summary(self, artifacts: CheckerArtifacts):
        """Print workflow summary."""
        print(f"\n{'='*80}")
        print(f"✅ Workflow Complete!")
        print(f"{'='*80}")
        print(f"Time taken: {artifacts.time_taken_seconds:.1f} seconds")
        print(f"\nSteps completed:")
        for step in artifacts.workflow_steps_completed:
            print(f"  ✅ {step}")
        
        if artifacts.manual_refinement_needed:
            print(f"\n⚠️  Manual refinement needed:")
            for item in artifacts.manual_refinement_needed:
                print(f"  📝 {item}")
            print(f"\nEstimated manual work: 10-30 minutes")
        else:
            print(f"\n🎉 No manual work needed - ready to test!")
        
        print(f"{'='*80}\n")
