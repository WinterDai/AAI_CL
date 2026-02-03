#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Verify All Checker Snapshots

Usage:
    python verify_all_snapshots.py                    # Verify all snapshots
    python verify_all_snapshots.py --modules 5.0      # Only verify specific module
    python verify_all_snapshots.py --update-failed    # Auto-update failed snapshots
    python verify_all_snapshots.py --show-diff        # Show detailed differences
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


class SnapshotVerifier:
    """Utility class for batch snapshot verification"""
    
    def __init__(self, update_failed: bool = False, show_diff: bool = False):
        self.manager = SnapshotManager()
        self.update_failed = update_failed
        self.show_diff = show_diff
        self.stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'missing': 0,
            'updated': 0,
            'errors': [],
            'failures': []
        }
    
    def discover_checkers(self, module_filter: str = None) -> Dict[str, List[Path]]:
        """Discover all Checker files (same logic as create_all_snapshots.py)"""
        checkers = {}
        
        for module_dir in _CHECK_MODULES_DIR.iterdir():
            if not module_dir.is_dir():
                continue
            if module_dir.name in ['common', '__pycache__']:
                continue
            
            if module_filter and not module_dir.name.startswith(module_filter):
                continue
            
            scripts_dir = module_dir / 'scripts'
            if not scripts_dir.exists():
                continue
            
            checker_files = []
            for pattern in ['IMP-*.py', 'IMP_*.py']:
                checker_files.extend(scripts_dir.glob(pattern))
                # Also search checker subdirectory
                checker_subdir = scripts_dir / 'checker'
                if checker_subdir.exists():
                    checker_files.extend(checker_subdir.glob(pattern))
            
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
        """Dynamically load Checker module"""
        module_name = checker_path.stem
        spec = importlib.util.spec_from_file_location(module_name, checker_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module: {checker_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return module
    
    def execute_checker(self, checker_path: Path) -> CheckResult:
        """Execute single Checker by calling its main() and reading output"""
        try:
            module_dir = checker_path.parents[2]
            outputs_dir = module_dir / 'outputs'
            checker_id = checker_path.stem
            module_name = module_dir.name
            output_file = outputs_dir / f'{module_name}.yaml'
            
            module = self.load_checker_module(checker_path)
            
            if hasattr(module, 'main'):
                import io
                import contextlib
                
                with contextlib.redirect_stdout(io.StringIO()), \
                     contextlib.redirect_stderr(io.StringIO()):
                    try:
                        module.main()
                    except SystemExit:
                        pass
            
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
            
            check_items = data.get('check_items', {})
            checker_data = check_items.get(checker_id, {})
            
            if not checker_data:
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
                    status = checker_data.get('status', 'unknown').lower()
                    self.is_pass = (status == 'pass')
                    self.value = checker_data.get('value', 'N/A')
                    
                    infos = checker_data.get('infos', [])
                    errors = checker_data.get('errors', [])
                    warnings = checker_data.get('warnings', [])
                    
                    self.details = []
                    self.has_pattern_items = len(errors) > 0 or len(warnings) > 0
                    self.has_waiver_value = 'waivers' in checker_data
                    
                    self.info_groups = {}
                    self.error_groups = {}
                    self.warn_groups = {}
                    
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
    
    def verify_snapshot_for_checker(self, checker_path: Path) -> Tuple[bool, str]:
        """
        Verify snapshot for single Checker
        
        Returns:
            (passed, status_message)
        """
        checker_name = checker_path.stem
        
        # Check if snapshot exists
        if not self.manager.snapshot_exists(checker_name):
            return False, "[MISSING] baseline missing"
        
        try:
            # Execute Checker
            print(f"  executing... ", end='', flush=True)
            result = self.execute_checker(checker_path)
            
            # Verify snapshot
            is_valid, diff_message = self.manager.verify_snapshot(checker_name, result)
            
            if is_valid:
                return True, "[OK] passed"
            else:
                # Record failure info
                failure_info = {
                    'checker': checker_name,
                    'path': str(checker_path),
                    'diff': diff_message
                }
                self.stats['failures'].append(failure_info)
                
                # Show diff if requested
                if self.show_diff:
                    print("\n" + "  " + diff_message.replace("\n", "\n  "))
                
                # Auto-update if requested
                if self.update_failed:
                    self.manager.update_snapshot(checker_name, result)
                    self.stats['updated'] += 1
                    return True, "[UPDATED] failed (updated)"
                
                return False, "[FAIL] failed"
                
        except Exception as e:
            error_msg = f"✗ error: {str(e)}"
            self.stats['errors'].append({
                'checker': checker_name,
                'path': str(checker_path),
                'error': str(e)
            })
            return False, error_msg
    
    def verify_all_snapshots(self, module_filter: str = None):
        """Batch verify all snapshots"""
        print("=" * 80)
        print("Batch Verify Checker Snapshots")
        print("=" * 80)
        print()
        
        # Discover all Checkers
        print("Scanning for Checker files...")
        checkers = self.discover_checkers(module_filter)
        
        if not checkers:
            print("[ERROR] No Checker files found")
            return
        
        total_count = sum(len(files) for files in checkers.values())
        self.stats['total'] = total_count
        
        print(f"Found {total_count} Checkers (across {len(checkers)} modules)")
        print()
        
        if self.update_failed:
            print("[AUTO-UPDATE] Failed snapshots will be updated")
            print()
        
        # Verify by module
        for module_name, checker_files in sorted(checkers.items()):
            print(f"[{module_name}] ({len(checker_files)} Checkers)")
            print("-" * 80)
            
            for idx, checker_path in enumerate(checker_files, 1):
                checker_name = checker_path.stem
                print(f"  [{idx}/{len(checker_files)}] {checker_name}... ", end='', flush=True)
                
                passed, message = self.verify_snapshot_for_checker(checker_path)
                print(message)
                
                if passed:
                    self.stats['passed'] += 1
                elif "missing" in message:
                    self.stats['missing'] += 1
                else:
                    self.stats['failed'] += 1
            
            print()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print verification summary"""
        print("=" * 80)
        print("Verification Summary")
        print("=" * 80)
        print(f"Total:     {self.stats['total']} Checkers")
        print(f"Passed:    {self.stats['passed']}")
        print(f"Failed:    {self.stats['failed']}")
        print(f"Missing:   {self.stats['missing']} (need to create baseline)")
        
        if self.stats['updated'] > 0:
            print(f"Updated:   {self.stats['updated']} (auto-updated)")
        
        print()
        
        if self.stats['errors']:
            print("Execution Errors:")
            for error in self.stats['errors']:
                print(f"  • {error['checker']}: {error['error']}")
            print()
        
        if self.stats['failures'] and not self.update_failed:
            print("Failed Checkers:")
            for failure in self.stats['failures'][:10]:  # Only show first 10
                print(f"  • {failure['checker']}")
                if self.show_diff:
                    print(f"    {failure['diff'][:200]}...")  # Truncate long diffs
            
            if len(self.stats['failures']) > 10:
                print(f"  ... and {len(self.stats['failures']) - 10} more failures")
            print()
            print("Tip: Use --show-diff to see detailed differences")
            print("Tip: Use --update-failed to auto-update failed snapshots")
            print()
        
        # Calculate success rate
        if self.stats['total'] > 0:
            success_rate = (self.stats['passed'] / self.stats['total'] * 100)
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success_rate == 100:
                print()
                print("All Checkers verified successfully!")
            elif success_rate >= 95:
                print()
                print("[WARNING] Few Checkers failed, please review")
            else:
                print()
                print("[ERROR] Many Checkers failed, please review code changes")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Batch verify all Checker snapshots',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify_all_snapshots.py                    # Verify all snapshots
  python verify_all_snapshots.py --modules 5.0      # Only verify 5.0_SYNTHESIS_CHECK
  python verify_all_snapshots.py --show-diff        # Show detailed differences
  python verify_all_snapshots.py --update-failed    # Auto-update failed snapshots
        """
    )
    
    parser.add_argument(
        '--modules',
        type=str,
        help='Only verify specific modules (e.g. "5.0" or "10.")'
    )
    
    parser.add_argument(
        '--update-failed',
        action='store_true',
        help='Auto-update failed snapshots'
    )
    
    parser.add_argument(
        '--show-diff',
        action='store_true',
        help='Show detailed diff information'
    )
    
    args = parser.parse_args()
    
    # Verify snapshots
    verifier = SnapshotVerifier(
        update_failed=args.update_failed,
        show_diff=args.show_diff
    )
    verifier.verify_all_snapshots(module_filter=args.modules)


if __name__ == '__main__':
    main()
