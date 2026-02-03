#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Create Snapshots for All Checkers

Usage:
    python create_all_snapshots.py                    # Create all snapshots
    python create_all_snapshots.py --modules 5.0      # Only create snapshots for specific module
    python create_all_snapshots.py --force            # Force overwrite existing snapshots
    python create_all_snapshots.py --dry-run          # Simulate run without creating
"""

import sys
import os
from pathlib import Path
import argparse
import importlib.util
from typing import List, Tuple, Dict
import json

# Add project paths
_CURRENT_DIR = Path(__file__).parent
_COMMON_DIR = _CURRENT_DIR.parent
_CHECK_MODULES_DIR = _COMMON_DIR.parent

sys.path.insert(0, str(_COMMON_DIR))
sys.path.insert(0, str(_CHECK_MODULES_DIR))

from snapshot_manager import SnapshotManager
from output_formatter import CheckResult


class SnapshotCreator:
    """Utility class for batch snapshot creation"""
    
    def __init__(self, force: bool = False, dry_run: bool = False):
        self.manager = SnapshotManager()
        self.force = force
        self.dry_run = dry_run
        self.stats = {
            'total': 0,
            'created': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
    
    def discover_checkers(self, module_filter: str = None) -> Dict[str, List[Path]]:
        """
        Discover all Checker files
        
        Args:
            module_filter: Optional module filter (e.g. "5.0" for 5.0_SYNTHESIS_CHECK only)
        
        Returns:
            {module_name: [checker_paths]}
        """
        checkers = {}
        
        # Scan all module directories
        for module_dir in _CHECK_MODULES_DIR.iterdir():
            if not module_dir.is_dir():
                continue
            if module_dir.name in ['common', '__pycache__']:
                continue
            
            # Apply module filter
            if module_filter and not module_dir.name.startswith(module_filter):
                continue
            
            # Find scripts directory
            scripts_dir = module_dir / 'scripts'
            if not scripts_dir.exists():
                continue
            
            # Find all IMP-*.py files (in scripts dir and checker subdir)
            checker_files = []
            for pattern in ['IMP-*.py', 'IMP_*.py']:
                checker_files.extend(scripts_dir.glob(pattern))
                # Also search checker subdirectory
                checker_subdir = scripts_dir / 'checker'
                if checker_subdir.exists():
                    checker_files.extend(checker_subdir.glob(pattern))
            
            # Filter out test files and template files
            checker_files = [
                f for f in checker_files 
                if not f.name.endswith('_test.py') 
                and not f.name.endswith('_templated.py')
                and f.name != '__init__.py'
            ]
            
            if checker_files:
                checkers[module_dir.name] = sorted(checker_files)
        
        return checkers
    
    def load_checker_module(self, checker_path: Path):
        """
        Dynamically load Checker module
        
        Args:
            checker_path: Checker file path
        
        Returns:
            Module object
        """
        module_name = checker_path.stem
        spec = importlib.util.spec_from_file_location(module_name, checker_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module: {checker_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return module
    
    def execute_checker(self, checker_path: Path) -> CheckResult:
        """
        Execute single Checker by calling its main() and reading output
        
        Args:
            checker_path: Checker file path
        
        Returns:
            CheckResult-like object
        """
        try:
            # Get module directory structure
            module_dir = checker_path.parents[2]
            outputs_dir = module_dir / 'outputs'
            checker_id = checker_path.stem
            module_name = module_dir.name
            
            # Output file is module-level YAML
            output_file = outputs_dir / f'{module_name}.yaml'
            
            # Dynamically load and run module
            module = self.load_checker_module(checker_path)
            
            # Call main() if it exists
            if hasattr(module, 'main'):
                import io
                import contextlib
                
                with contextlib.redirect_stdout(io.StringIO()), \
                     contextlib.redirect_stderr(io.StringIO()):
                    try:
                        module.main()
                    except SystemExit:
                        pass
            
            # Read output file if it was created/updated
            if output_file.exists():
                return self._parse_yaml_output(output_file, checker_id)
            else:
                class MinimalResult:
                    def __init__(self):
                        self.is_pass = True
                        self.value = "N/A"
                        self.details = []
                        self.has_pattern_items = False
                        self.has_waiver_value = False
                        self.info_groups = {}
                        self.error_groups = {}
                        self.warn_groups = {}
                return MinimalResult()
            
        except Exception as e:
            class ErrorResult:
                def __init__(self):
                    self.is_pass = False
                    self.value = "ERROR"
                    self.details = []
                    self.has_pattern_items = False
                    self.has_waiver_value = False
                    self.info_groups = {}
                    self.error_groups = {"execution_error": [str(e)]}
                    self.warn_groups = {}
            return ErrorResult()
    
    def _parse_yaml_output(self, output_path: Path, checker_id: str):
        """Parse YAML output file to extract checker result"""
        try:
            import yaml
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Find this checker's entry
            check_items = data.get('check_items', {})
            checker_data = check_items.get(checker_id, {})
            
            if not checker_data:
                # Checker not found in output
                class MinimalResult:
                    def __init__(self):
                        self.is_pass = True
                        self.value = "N/A"
                        self.details = []
                        self.has_pattern_items = False
                        self.has_waiver_value = False
                        self.info_groups = {}
                        self.error_groups = {}
                        self.warn_groups = {}
                return MinimalResult()
            
            class ParsedResult:
                def __init__(self):
                    # Extract status
                    status = checker_data.get('status', 'unknown').lower()
                    self.is_pass = (status == 'pass')
                    
                    # Extract value if present
                    self.value = checker_data.get('value', 'N/A')
                    
                    # Get detailed items
                    infos = checker_data.get('infos', [])
                    errors = checker_data.get('errors', [])
                    warnings = checker_data.get('warnings', [])
                    
                    self.details = []
                    self.has_pattern_items = len(errors) > 0 or len(warnings) > 0
                    self.has_waiver_value = 'waivers' in checker_data
                    
                    # Build detailed groups with actual items
                    self.info_groups = {}
                    self.error_groups = {}
                    self.warn_groups = {}
                    
                    # Group infos by reason/detail
                    if infos:
                        info_items = []
                        for item in infos:
                            info_items.append({
                                'detail': item.get('detail', ''),
                                'reason': item.get('reason', ''),
                                'source_file': item.get('source_file', ''),
                                'source_line': item.get('source_line', 0)
                            })
                        self.info_groups = {'items': info_items}
                    
                    # Group errors by reason/detail
                    if errors:
                        error_items = []
                        for item in errors:
                            error_items.append({
                                'detail': item.get('detail', ''),
                                'reason': item.get('reason', ''),
                                'source_file': item.get('source_file', ''),
                                'source_line': item.get('source_line', 0)
                            })
                        self.error_groups = {'items': error_items}
                    
                    # Group warnings by reason/detail
                    if warnings:
                        warn_items = []
                        for item in warnings:
                            warn_items.append({
                                'detail': item.get('detail', ''),
                                'reason': item.get('reason', ''),
                                'source_file': item.get('source_file', ''),
                                'source_line': item.get('source_line', 0)
                            })
                        self.warn_groups = {'items': warn_items}
            
            return ParsedResult()
            
        except Exception as e:
            class ErrorResult:
                def __init__(self):
                    self.is_pass = False
                    self.value = "ERROR"
                    self.details = []
                    self.has_pattern_items = False
                    self.has_waiver_value = False
                    self.info_groups = {}
                    self.error_groups = {"parse_error": [str(e)]}
                    self.warn_groups = {}
            return ErrorResult()
    
    def create_snapshot_for_checker(self, checker_path: Path) -> Tuple[bool, str]:
        """
        Create snapshot for single Checker
        
        Args:
            checker_path: Checker file path
        
        Returns:
            (success, message)
        """
        checker_name = checker_path.stem
        
        # Check if already exists
        if not self.force and self.manager.snapshot_exists(checker_name):
            return False, "exists (skipped)"
        
        if self.dry_run:
            return True, "simulated (dry-run)"
        
        try:
            # Execute Checker
            print(f"  executing... ", end='', flush=True)
            result = self.execute_checker(checker_path)
            
            # Create snapshot
            self.manager.create_snapshot(checker_name, result)
            return True, "[OK] created"
            
        except Exception as e:
            error_msg = f"[ERROR] failed: {str(e)}"
            self.stats['errors'].append({
                'checker': checker_name,
                'path': str(checker_path),
                'error': str(e)
            })
            return False, error_msg
    
    def create_all_snapshots(self, module_filter: str = None):
        """
        Batch create all snapshots
        
        Args:
            module_filter: Optional module filter
        """
        print("=" * 80)
        print("Batch Create Checker Snapshots")
        print("=" * 80)
        print()
        
        # Discover all Checkers
        print("Scanning for Checker files...")
        checkers = self.discover_checkers(module_filter)
        
        if not checkers:
            print("[ERROR] No Checker files found")
            return
        
        # Count total
        total_count = sum(len(files) for files in checkers.values())
        self.stats['total'] = total_count
        
        print(f"Found {total_count} Checkers (across {len(checkers)} modules)")
        print()
        
        if self.dry_run:
            print("[DRY-RUN] Snapshots will not be created")
            print()
        
        # Process by module
        for module_name, checker_files in sorted(checkers.items()):
            print(f"[{module_name}] ({len(checker_files)} Checkers)")
            print("-" * 80)
            
            for idx, checker_path in enumerate(checker_files, 1):
                checker_name = checker_path.stem
                print(f"  [{idx}/{len(checker_files)}] {checker_name}... ", end='', flush=True)
                
                success, message = self.create_snapshot_for_checker(checker_path)
                print(message)
                
                if success:
                    self.stats['created'] += 1
                elif "exists" in message or "skipped" in message:
                    self.stats['skipped'] += 1
                else:
                    self.stats['failed'] += 1
            
            print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print execution summary"""
        print("=" * 80)
        print("Execution Summary")
        print("=" * 80)
        print(f"Total:     {self.stats['total']} Checkers")
        print(f"Created:   {self.stats['created']} snapshots")
        print(f"Skipped:   {self.stats['skipped']} (already exist)")
        print(f"Failed:    {self.stats['failed']}")
        print()
        
        if self.stats['errors']:
            print("Failed Checkers:")
            for error in self.stats['errors']:
                print(f"  • {error['checker']}: {error['error']}")
            print()
        
        success_rate = (self.stats['created'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if not self.dry_run and self.stats['created'] > 0:
            print()
            print(f"Snapshots saved to: {self.manager.snapshot_file}")
            print(f"  Run 'python verify_all_snapshots.py' to verify")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Batch create snapshots for all Checkers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_all_snapshots.py                    # Create all snapshots
  python create_all_snapshots.py --modules 5.0      # Only process 5.0_SYNTHESIS_CHECK
  python create_all_snapshots.py --modules 10.      # Process all 10.x modules
  python create_all_snapshots.py --force            # Overwrite existing snapshots
  python create_all_snapshots.py --dry-run          # Simulate run
        """
    )
    
    parser.add_argument(
        '--modules',
        type=str,
        help='Only process specific modules (e.g. "5.0" or "10.")'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing snapshots'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate run without creating snapshots'
    )
    
    args = parser.parse_args()
    
    # Create snapshots
    creator = SnapshotCreator(force=args.force, dry_run=args.dry_run)
    creator.create_all_snapshots(module_filter=args.modules)


if __name__ == '__main__':
    main()
