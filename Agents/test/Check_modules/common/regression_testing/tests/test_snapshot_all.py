"""
批量快照测试 - 自动化测试所有Checker

使用场景：
1. 迁移前：运行原版所有Checker，创建快照基线
2. 迁移后：运行模板版Checker，对比输出是否一致
3. 维护期：定期运行验证没有破坏性变更

Author: yyin
Date: 2025-12-08
"""

import unittest
import sys
from pathlib import Path
from typing import Dict, Any, List
import importlib
import json

# Add paths
_TEST_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _TEST_DIR.parents[3]
_COMMON_DIR = _WORKSPACE_ROOT / 'Check_modules' / 'common'
_REGRESSION_DIR = _COMMON_DIR / 'regression_testing'

if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))
if str(_REGRESSION_DIR) not in sys.path:
    sys.path.insert(0, str(_REGRESSION_DIR))

from snapshot_manager import SnapshotManager


class TestAllCheckersSnapshot(unittest.TestCase):
    """
    批量快照测试
    
    自动发现并测试所有Checker，对比输出与快照的一致性
    """
    
    @classmethod
    def setUpClass(cls):
        cls.snapshot_manager = SnapshotManager()
        cls.check_modules_dir = _WORKSPACE_ROOT / 'Check_modules'
        
    def discover_checkers(self) -> List[Dict[str, Any]]:
        """
        自动发现所有Checker脚本
        
        Returns:
            List of checker metadata: [{'id': 'IMP-5-0-0-00', 'path': Path, 'module': '5.0_SYNTHESIS_CHECK'}, ...]
        """
        checkers = []
        
        # 扫描所有模块目录
        for module_dir in self.check_modules_dir.glob('*_CHECK'):
            if not module_dir.is_dir():
                continue
            
            # Find scripts/checker/ directory
            checker_dir = module_dir / 'scripts' / 'checker'
            if not checker_dir.exists():
                continue
            
            # Find all IMP-*.py files
            for checker_file in checker_dir.glob('IMP-*.py'):
                checker_id = checker_file.stem  # 'IMP-5-0-0-00'
                
                checkers.append({
                    'id': checker_id,
                    'path': checker_file,
                    'module': module_dir.name
                })
        
        return checkers
    
    def test_snapshot_manager_initialized(self):
        """Test: Snapshot manager is initialized"""
        self.assertIsNotNone(self.snapshot_manager)
        self.assertTrue(self.snapshot_manager.snapshot_file.parent.exists())
    
    def test_discover_all_checkers(self):
        """Test: Auto-discover all Checkers"""
        checkers = self.discover_checkers()
        
        print(f"\nDiscovered {len(checkers)} checkers:")
        
        # 按模块分组统计
        modules = {}
        for checker in checkers:
            module = checker['module']
            if module not in modules:
                modules[module] = []
            modules[module].append(checker['id'])
        
        for module, checker_ids in sorted(modules.items()):
            print(f"  {module}: {len(checker_ids)} checkers")
        
        self.assertGreater(len(checkers), 0, "应该至少发现1个Checker")
    
    def test_verify_existing_snapshots(self):
        """Test: Verify integrity of existing snapshots"""
        snapshots = self.snapshot_manager.list_snapshots()
        
        if not snapshots:
            self.skipTest("No snapshots found - run create_snapshots first")
        
        print(f"\nFound {len(snapshots)} existing snapshots")
        
        # 验证每个快照文件的结构
        for checker_id in snapshots:
            info = self.snapshot_manager.get_snapshot_info(checker_id)
            
            self.assertIsNotNone(info, f"{checker_id} snapshot info should exist")
            self.assertIn('created_at', info)
            self.assertIn('content_hash', info)
            self.assertIn('result_summary', info)


class TestSnapshotWorkflow(unittest.TestCase):
    """
    测试快照工作流程
    
    演示如何创建和验证快照
    """
    
    def test_create_and_verify_snapshot(self):
        """Test: Create snapshot and verify"""
        from output_formatter import create_check_result, DetailItem, Severity
        
        # 创建模拟的CheckResult
        result = create_check_result(
            value=10,
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=[
                DetailItem(
                    severity=Severity.INFO,
                    name="test_item",
                    line_number=1,
                    file_path="test.log",
                    reason="Test reason"
                )
            ]
        )
        
        manager = SnapshotManager()
        
        # 创建快照
        checker_id = "TEST-SNAPSHOT-01"
        snapshot_file = manager.create_snapshot(
            checker_id,
            result,
            metadata={'test': True}
        )
        
        self.assertTrue(snapshot_file.exists())
        
        # 验证快照
        is_match, diff = manager.verify_snapshot(checker_id, result)
        self.assertTrue(is_match, "Output should match snapshot")
        self.assertIsNone(diff)
        
        # 修改结果
        result.value = 20  # 改变value
        is_match, diff = manager.verify_snapshot(checker_id, result)
        self.assertFalse(is_match, "Modified output should not match")
        self.assertIsNotNone(diff)
        self.assertIn('value', diff)
        
        # 清理
        snapshot_file.unlink()


# ============================================================================
# 快照创建工具
# ============================================================================

def create_baseline_snapshots():
    """
    创建基线快照 - 为所有现有Checker创建快照
    
    用法：
        python -m tests.test_snapshot_all --create-baseline
    """
    print("=" * 80)
    print("Creating Baseline Snapshots")
    print("=" * 80)
    
    # TODO: 实现实际的Checker运行逻辑
    # 1. 发现所有Checker
    # 2. 为每个Checker准备测试数据
    # 3. 运行Checker
    # 4. 创建快照
    
    test = TestAllCheckersSnapshot()
    test.setUpClass()
    
    checkers = test.discover_checkers()
    print(f"\nFound {len(checkers)} checkers to snapshot")
    
    print("\n⚠️  Note: Actual checker execution not implemented yet.")
    print("To create snapshots, you need to:")
    print("1. Prepare test data for each checker")
    print("2. Run each checker with the test data")
    print("3. Call snapshot_manager.create_snapshot() with the result")


def verify_against_snapshots():
    """
    验证所有Checker输出与快照的一致性
    
    用法：
        python -m tests.test_snapshot_all --verify
    """
    print("=" * 80)
    print("Verifying Against Snapshots")
    print("=" * 80)
    
    manager = SnapshotManager()
    snapshots = manager.list_snapshots()
    
    if not snapshots:
        print("\n❌ No snapshots found. Run --create-baseline first.")
        return False
    
    print(f"\nFound {len(snapshots)} snapshots to verify")
    
    # TODO: 实现实际的验证逻辑
    print("\n⚠️  Note: Actual verification not implemented yet.")
    print("To verify snapshots, you need to:")
    print("1. Run each checker with the same test data")
    print("2. Call snapshot_manager.verify_snapshot() with the result")
    print("3. Report any differences")
    
    return True


if __name__ == '__main__':
    import sys
    
    if '--create-baseline' in sys.argv:
        create_baseline_snapshots()
    elif '--verify' in sys.argv:
        verify_against_snapshots()
    else:
        # 运行单元测试
        unittest.main(argv=[sys.argv[0]])
