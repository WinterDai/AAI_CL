"""High-level orchestrator for checker generation workflow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Add parent dir to path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

from .models import CheckerArtifacts, WorkflowConfig
from .pipeline import CheckerGenerationPipeline


class CheckerWorkflowOrchestrator:
    """
    High-level API for checker generation.
    
    Provides simple interfaces for common use cases:
    - generate_full_checker(): Complete workflow
    - generate_code_only(): Skip README/test
    - interactive_generation(): Step-by-step with user prompts
    """
    
    @staticmethod
    def generate_full_checker(
        item_id: str,
        module: str,
        *,
        item_desc: Optional[str] = None,
        input_files: Optional[list[str]] = None,
        use_llm: bool = True,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        interactive: bool = False,
        output_dir: Optional[Path] = None,
    ) -> CheckerArtifacts:
        """
        Generate complete checker with all artifacts.
        
        Args:
            item_id: Checker item ID (e.g., IMP-10-0-0-11)
            module: Module name (e.g., 10.0_STA_DCD_CHECK)
            item_desc: Optional description override
            input_files: Optional input files override
            use_llm: Whether to use LLM for generation
            llm_provider: LLM provider (openai or anthropic)
            llm_model: Optional model override
            interactive: Interactive mode with prompts
            output_dir: Optional output directory
        
        Returns:
            CheckerArtifacts containing all generated content
        """
        config = WorkflowConfig(
            item_id=item_id,
            module=module,
            item_desc=item_desc,
            input_files=input_files or [],
            use_llm=use_llm,
            llm_provider=llm_provider,
            llm_model=llm_model,
            interactive=interactive,
            output_dir=output_dir,
        )
        
        pipeline = CheckerGenerationPipeline(config)
        artifacts = pipeline.run_full_workflow()
        
        # Save artifacts if output_dir specified
        if output_dir:
            CheckerWorkflowOrchestrator._save_artifacts(artifacts, output_dir)
        
        return artifacts
    
    @staticmethod
    def generate_code_only(
        item_id: str,
        module: str,
        *,
        use_llm: bool = True,
        llm_provider: str = "openai",
    ) -> str:
        """
        Generate only the checker code, skip README and test setup.
        
        Faster workflow for experienced developers who only need the code template.
        
        Returns:
            Generated checker code as string
        """
        config = WorkflowConfig(
            item_id=item_id,
            module=module,
            use_llm=use_llm,
            llm_provider=llm_provider,
            skip_readme=True,
            skip_test_setup=True,
        )
        
        pipeline = CheckerGenerationPipeline(config)
        artifacts = pipeline.run_full_workflow()
        
        return artifacts.code or ""
    
    @staticmethod
    def interactive_generation(
        item_id: str,
        module: str,
    ) -> CheckerArtifacts:
        """
        Interactive mode: prompts user at each step.
        
        Useful for learning the workflow or when customization is needed.
        """
        config = WorkflowConfig(
            item_id=item_id,
            module=module,
            interactive=True,
            use_llm=True,
        )
        
        pipeline = CheckerGenerationPipeline(config)
        
        print("\n" + "="*80)
        print("🎯 Interactive Checker Generation")
        print("="*80)
        print("\nYou will be prompted at each step.")
        print("Press Enter to continue with defaults, or provide custom input.\n")
        
        # TODO: Add interactive prompts at each step
        artifacts = pipeline.run_full_workflow()
        
        return artifacts
    
    @staticmethod
    def analyze_files_only(
        module: str,
        input_files: list[str],
    ) -> list[dict]:
        """
        Run only Step 2.5 (file analysis) without generating code.
        
        Useful for understanding input file formats before implementation.
        """
        config = WorkflowConfig(
            item_id="ANALYSIS_ONLY",
            module=module,
            input_files=input_files,
            skip_readme=True,
            skip_test_setup=True,
            use_llm=False,
        )
        
        pipeline = CheckerGenerationPipeline(config)
        
        # Load config
        config_data = pipeline.step1_update_config()
        config_data['input_files'] = input_files
        
        # Run analysis
        analysis_results = pipeline.step2_5_analyze_files(config_data)
        
        # Print results
        print("\n" + "="*80)
        print("📊 File Analysis Results")
        print("="*80)
        
        for idx, analysis in enumerate(analysis_results, 1):
            print(f"\n[File {idx}] {analysis.get('file_name', 'Unknown')}")
            print(f"  Type: {analysis.get('file_type', 'Unknown')}")
            print(f"  Exists: {analysis.get('exists', False)}")
            
            if analysis.get('patterns'):
                print(f"  Patterns: {', '.join(analysis['patterns'][:5])}")
            
            if analysis.get('parsing_strategy'):
                print(f"  Strategy: {analysis['parsing_strategy']}")
            
            sample = analysis.get('sample_data', '')
            if sample:
                print(f"\n  Sample Data (first 300 chars):")
                print("  " + "-"*70)
                for line in sample[:300].split('\n')[:10]:
                    print(f"  {line}")
                print("  " + "-"*70)
        
        print("\n" + "="*80 + "\n")
        
        return analysis_results
    
    @staticmethod
    def _save_artifacts(artifacts: CheckerArtifacts, output_dir: Path):
        """Save generated artifacts to disk."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save README
        if artifacts.readme:
            readme_file = output_dir / "README.md"
            readme_file.write_text(artifacts.readme, encoding='utf-8')
            print(f"💾 Saved README: {readme_file}")
        
        # Save code
        if artifacts.code:
            code_file = output_dir / f"{artifacts.config.get('item_id', 'checker')}.py"
            code_file.write_text(artifacts.code, encoding='utf-8')
            print(f"💾 Saved code: {code_file}")
        
        # Save artifacts metadata
        import json
        metadata_file = output_dir / "artifacts.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(artifacts.to_dict(), f, indent=2, default=str)
        print(f"💾 Saved metadata: {metadata_file}")
