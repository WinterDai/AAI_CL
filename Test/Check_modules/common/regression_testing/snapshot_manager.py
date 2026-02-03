"""
Snapshot Manager - Automated Snapshot Testing System

Features:
1. Create output snapshots for all Checkers
2. Auto-detect Checker changes and verify output consistency
3. Support snapshot updates and diff comparison

Use Cases:
- Pre-migration: Create baseline snapshots for original Checkers
- Post-migration: Compare template version outputs for consistency
- Maintenance: Prevent code changes from breaking existing functionality

Author: yyin
Date: 2025-12-08
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import difflib


class SnapshotManager:
    """Snapshot Manager - Manages output snapshots for all Checkers"""
    
    def __init__(self, snapshot_file: Optional[Path] = None):
        """
        Initialize snapshot manager
        
        Args:
            snapshot_file: Snapshot storage file, defaults to tests/data/snapshots.json
        """
        if snapshot_file is None:
            _THIS_DIR = Path(__file__).resolve().parent
            snapshot_dir = _THIS_DIR / 'tests' / 'data'
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            snapshot_file = snapshot_dir / 'snapshots.json'
        
        self.snapshot_file = Path(snapshot_file)
        self.snapshots = self._load_snapshots()
    
    def _load_snapshots(self) -> Dict[str, Any]:
        """Load all snapshots from consolidated file"""
        if self.snapshot_file.exists():
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'snapshots': {}
        }
    
    def _save_snapshots(self):
        """Save all snapshots to consolidated file"""
        with open(self.snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots, f, indent=2, ensure_ascii=False)
    
    def snapshot_exists(self, checker_name: str) -> bool:
        """
        Check if snapshot exists
        
        Args:
            checker_name: Checker name
            
        Returns:
            True if snapshot exists
        """
        return checker_name in self.snapshots.get('snapshots', {})
    
    def _normalize_result(self, result: Any) -> Dict[str, Any]:
        """
        Normalize CheckResult object to serializable dict
        
        Extract key fields, ignore unimportant differences (timestamps, path formats)
        """
        if hasattr(result, '__dict__'):
            result = result.__dict__
        
        normalized = {
            'value': result.get('value'),
            'is_pass': result.get('is_pass'),
            'has_pattern_items': result.get('has_pattern_items', False),
            'has_waiver_value': result.get('has_waiver_value', False),
            'details': [],
            'info_groups': result.get('info_groups', {}),
            'error_groups': result.get('error_groups', {}),
            'warn_groups': result.get('warn_groups', {})
        }
        
        # Normalize details
        details = result.get('details', [])
        for detail in details:
            if hasattr(detail, '__dict__'):
                detail = detail.__dict__
            
            normalized['details'].append({
                'severity': str(detail.get('severity', '')),
                'name': detail.get('name', ''),
                'reason': detail.get('reason', ''),
                # Ignore line_number and file_path (may differ by environment)
            })
        
        # Sort for consistency
        normalized['details'].sort(key=lambda x: (x['severity'], x['name']))
        
        return normalized
    
    def create_snapshot(
        self,
        checker_id: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Create snapshot
        
        Args:
            checker_id: Checker ID (e.g. 'IMP-5-0-0-00')
            result: CheckResult object
            metadata: Additional metadata (version, author, etc.)
        
        Returns:
            Snapshot file path
        """
        # Normalize output
        normalized = self._normalize_result(result)
        
        # Calculate hash
        content_hash = hashlib.sha256(
            json.dumps(normalized, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        # Build snapshot data
        snapshot_data = {
            'checker_id': checker_id,
            'created_at': datetime.now().isoformat(),
            'content_hash': content_hash,
            'result': normalized,
            'metadata': metadata or {}
        }
        
        # Save to consolidated snapshots
        self.snapshots['snapshots'][checker_id] = snapshot_data
        self._save_snapshots()
        
        return self.snapshot_file
    
    def verify_snapshot(
        self,
        checker_id: str,
        result: Any,
        strict: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify if output matches snapshot
        
        Args:
            checker_id: Checker ID
            result: Current CheckResult
            strict: Strict mode (compare all fields strictly)
        
        Returns:
            (is_match, diff_message)
            - is_match: Whether it matches
            - diff_message: Diff message (if mismatch)
        """
        # Check if snapshot exists
        if checker_id not in self.snapshots['snapshots']:
            return False, f'Snapshot not found for {checker_id}'
        
        # Load snapshot
        snapshot_data = self.snapshots['snapshots'][checker_id]
        
        # Normalize current result
        current = self._normalize_result(result)
        expected = snapshot_data['result']
        
        # Compare
        diff_report = self._compare_results(expected, current, strict)
        
        if not diff_report:
            return True, None
        
        # Generate diff message
        diff_message = self._format_diff(diff_report)
        return False, diff_message
    
    def _compare_results(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any],
        strict: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Compare two results
        
        Returns:
            Diff report, None if identical
        """
        differences = {}
        
        # Compare key fields
        key_fields = ['value', 'is_pass', 'has_pattern_items', 'has_waiver_value']
        for field in key_fields:
            if expected.get(field) != actual.get(field):
                differences[field] = {
                    'expected': expected.get(field),
                    'actual': actual.get(field)
                }
        
        # Compare details count
        if len(expected.get('details', [])) != len(actual.get('details', [])):
            differences['details_count'] = {
                'expected': len(expected.get('details', [])),
                'actual': len(actual.get('details', []))
            }
        
        # Compare details content
        exp_details = expected.get('details', [])
        act_details = actual.get('details', [])
        
        detail_diffs = []
        for i, (exp, act) in enumerate(zip(exp_details, act_details)):
            if exp != act:
                detail_diffs.append({
                    'index': i,
                    'expected': exp,
                    'actual': act
                })
        
        if detail_diffs:
            differences['details'] = detail_diffs[:5]  # Only show first 5 diffs
        
        # Compare groups
        for group_type in ['info_groups', 'error_groups', 'warn_groups']:
            exp_groups = expected.get(group_type, {})
            act_groups = actual.get(group_type, {})
            
            if exp_groups != act_groups:
                differences[group_type] = {
                    'expected_keys': list(exp_groups.keys()),
                    'actual_keys': list(act_groups.keys())
                }
        
        return differences if differences else None
    
    def _format_diff(self, diff_report: Dict[str, Any]) -> str:
        """Format diff report as human-readable string"""
        lines = []
        
        for field, diff in diff_report.items():
            if field == 'details':
                lines.append(f"Details differences ({len(diff)} items):")
                for item in diff[:3]:  # Only show first 3
                    lines.append(f"  [{item['index']}]:")
                    lines.append(f"    Expected: {item['expected']}")
                    lines.append(f"    Actual:   {item['actual']}")
            else:
                lines.append(f"{field}:")
                lines.append(f"  Expected: {diff.get('expected')}")
                lines.append(f"  Actual:   {diff.get('actual')}")
        
        return '\n'.join(lines)
    
    def verify_all(
        self,
        results: Dict[str, Any],
        strict: bool = False
    ) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Batch verify all snapshots
        
        Args:
            results: {checker_id: result} dict
            strict: Strict mode
        
        Returns:
            {checker_id: (is_match, diff_message)}
        """
        verification_results = {}
        
        for checker_id, result in results.items():
            is_match, diff = self.verify_snapshot(checker_id, result, strict)
            verification_results[checker_id] = (is_match, diff)
        
        return verification_results
    
    def update_snapshot(self, checker_id: str, result: Any) -> Path:
        """
        Update existing snapshot
        
        Args:
            checker_id: Checker ID
            result: New CheckResult
        
        Returns:
            Snapshot file path
        """
        return self.create_snapshot(checker_id, result)
    
    def diff_snapshot(self, checker_id: str, result: Any) -> str:
        """
        Generate human-readable diff report
        
        Args:
            checker_id: Checker ID
            result: Current CheckResult
        
        Returns:
            Formatted diff report string
        """
        is_match, diff_message = self.verify_snapshot(checker_id, result)
        
        if is_match:
            return f"✓ {checker_id}: Output matches snapshot"
        
        return f"✗ {checker_id}: Output differs from snapshot\n{diff_message}"
    
    def list_snapshots(self) -> List[str]:
        """List all Checker IDs with snapshots"""
        return list(self.snapshots['snapshots'].keys())
    
    def get_snapshot_info(self, checker_id: str) -> Optional[Dict[str, Any]]:
        """Get snapshot information"""
        if checker_id not in self.snapshots['snapshots']:
            return None
        
        snapshot_data = self.snapshots['snapshots'][checker_id]
        
        return {
            'checker_id': checker_id,
            'created_at': snapshot_data.get('created_at'),
            'content_hash': snapshot_data.get('content_hash'),
            'metadata': snapshot_data.get('metadata', {}),
            'result_summary': {
                'is_pass': snapshot_data['result'].get('is_pass'),
                'value': snapshot_data['result'].get('value'),
                'detail_count': len(snapshot_data['result'].get('details', []))
            }
        }


# ============================================================================
# CLI Utility Functions
# ============================================================================

def create_all_snapshots(checker_results: Dict[str, Any]) -> None:
    """
    Create snapshots for all Checkers
    
    Args:
        checker_results: {checker_id: result} dict
    """
    manager = SnapshotManager()
    
    print(f"Creating snapshots for {len(checker_results)} checkers...")
    
    for checker_id, result in checker_results.items():
        snapshot_file = manager.create_snapshot(checker_id, result)
        print(f"  ✓ {checker_id}")
    
    print(f"\nDone! Created {len(checker_results)} snapshots in {manager.snapshot_file}")


def verify_all_snapshots(checker_results: Dict[str, Any]) -> bool:
    """
    Verify all Checker outputs
    
    Args:
        checker_results: {checker_id: result} dict
    
    Returns:
        Whether all passed
    """
    manager = SnapshotManager()
    
    print(f"Verifying {len(checker_results)} checkers...")
    
    verification_results = manager.verify_all(checker_results)
    
    passed = 0
    failed = 0
    
    for checker_id, (is_match, diff) in verification_results.items():
        if is_match:
            print(f"  ✓ {checker_id}")
            passed += 1
        else:
            print(f"  ✗ {checker_id}")
            if diff:
                print(f"    {diff[:200]}...")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == '__main__':
    # Example usage
    manager = SnapshotManager()
    print(f"Snapshot file: {manager.snapshot_file}")
    print(f"Snapshots: {len(manager.list_snapshots())}")
