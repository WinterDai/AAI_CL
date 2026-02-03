"""
Baseline Manager for Regression Testing.

Manages test result baselines:
- Save current test results as baseline
- Load baseline for comparison
- Track baseline history
- Checksum verification

Storage: test_baseline/{item_id}/
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import hashlib
import shutil


class BaselineManager:
    """Manage test result baselines."""
    
    def __init__(self, item_id: str):
        """
        Initialize baseline manager.
        
        Args:
            item_id: Checker ID
        """
        self.item_id = item_id
        
        # Setup paths
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        self.workspace_root = paths.workspace_root
        
        # Baseline directory
        self.baseline_dir = self.workspace_root / "test_baseline" / item_id
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
    
    def save_baseline(
        self,
        results_dir: Path,
        description: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Path:
        """
        Save test results as baseline.
        
        Args:
            results_dir: Directory containing test results
            description: Optional baseline description
            author: Optional author name
        
        Returns:
            Path to saved baseline directory
        """
        if not results_dir.exists():
            raise FileNotFoundError(f"Results directory not found: {results_dir}")
        
        results_file = results_dir / "test_results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        # Load results to get summary
        with open(results_file, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
        
        # Create baseline manifest
        manifest = {
            "item_id": self.item_id,
            "baseline_created": datetime.now().isoformat(),
            "description": description or "Baseline from test run",
            "author": author or "unknown",
            "source_results": str(results_dir.relative_to(self.workspace_root)),
            "summary": results_data["summary"],
            "test_types": list(results_data["test_results"].keys()),
            "checksums": self._compute_checksums(results_dir),
        }
        
        # Save manifest
        manifest_file = self.baseline_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        # Copy test results
        baseline_results_file = self.baseline_dir / "test_results.json"
        shutil.copy(results_file, baseline_results_file)
        
        # Copy all test outputs
        for output_file in results_dir.glob("*_output.txt"):
            shutil.copy(output_file, self.baseline_dir / output_file.name)
        
        # Copy consolidated reports
        for report_file in results_dir.glob("consolidated_report.*"):
            shutil.copy(report_file, self.baseline_dir / report_file.name)
        
        print(f"✅ Baseline saved: {self.baseline_dir.relative_to(self.workspace_root)}")
        print(f"   Tests: {len(manifest['test_types'])}")
        print(f"   Pass Rate: {manifest['summary']['pass_rate']}")
        
        return self.baseline_dir
    
    def load_baseline(self) -> Optional[Dict[str, Any]]:
        """
        Load baseline for this checker.
        
        Returns:
            Baseline data dict, or None if no baseline exists
        """
        manifest_file = self.baseline_dir / "manifest.json"
        if not manifest_file.exists():
            return None
        
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Load test results
        results_file = self.baseline_dir / "test_results.json"
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                test_results = json.load(f)
            
            manifest["test_results"] = test_results
        
        return manifest
    
    def verify_baseline_integrity(self) -> bool:
        """
        Verify baseline integrity using checksums.
        
        Returns:
            True if baseline is intact, False otherwise
        """
        manifest = self.load_baseline()
        if not manifest:
            return False
        
        stored_checksums = manifest.get("checksums", {})
        current_checksums = self._compute_checksums(self.baseline_dir)
        
        # Compare checksums
        for filename, stored_checksum in stored_checksums.items():
            current_checksum = current_checksums.get(filename)
            if current_checksum != stored_checksum:
                print(f"⚠️  Checksum mismatch: {filename}")
                return False
        
        return True
    
    def list_baseline_history(self) -> None:
        """Print baseline history information."""
        manifest = self.load_baseline()
        
        if not manifest:
            print(f"No baseline found for {self.item_id}")
            return
        
        print(f"\n📦 Baseline for {self.item_id}")
        print(f"{'='*80}")
        print(f"Created: {manifest['baseline_created']}")
        print(f"Author: {manifest['author']}")
        print(f"Description: {manifest['description']}")
        print(f"\nTest Summary:")
        print(f"  Total Tests: {manifest['summary']['total_tests']}")
        print(f"  Passed: {manifest['summary']['passed']}")
        print(f"  Failed: {manifest['summary']['failed']}")
        print(f"  Pass Rate: {manifest['summary']['pass_rate']}")
        print(f"\nTest Types: {', '.join(manifest['test_types'])}")
        
        # Verify integrity
        if self.verify_baseline_integrity():
            print(f"\n✅ Baseline integrity verified")
        else:
            print(f"\n⚠️  Baseline integrity check failed")
    
    def _compute_checksums(self, directory: Path) -> Dict[str, str]:
        """
        Compute checksums for all files in directory.
        
        Args:
            directory: Directory to scan
        
        Returns:
            Dict mapping filename to SHA256 checksum
        """
        checksums = {}
        
        for file_path in directory.glob("*.json"):
            checksums[file_path.name] = self._file_checksum(file_path)
        
        for file_path in directory.glob("*.txt"):
            checksums[file_path.name] = self._file_checksum(file_path)
        
        return checksums
    
    def _file_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum for a file."""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()


def save_baseline(
    item_id: str,
    results_dir: Path,
    description: Optional[str] = None,
    author: Optional[str] = None,
) -> Path:
    """
    Convenience function to save baseline.
    
    Args:
        item_id: Checker ID
        results_dir: Directory containing test results
        description: Optional baseline description
        author: Optional author name
    
    Returns:
        Path to baseline directory
    """
    manager = BaselineManager(item_id)
    return manager.save_baseline(results_dir, description, author)


def load_baseline(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load baseline.
    
    Args:
        item_id: Checker ID
    
    Returns:
        Baseline data dict, or None if no baseline exists
    """
    manager = BaselineManager(item_id)
    return manager.load_baseline()


if __name__ == "__main__":
    # Baseline manager CLI
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python baseline_manager.py save <item_id> <results_dir> [description]")
        print("  python baseline_manager.py load <item_id>")
        print("  python baseline_manager.py list <item_id>")
        print("\nExamples:")
        print("  python baseline_manager.py save IMP-9-0-0-07 Work/test_results/IMP-9-0-0-07/20250126_143052")
        print("  python baseline_manager.py load IMP-9-0-0-07")
        print("  python baseline_manager.py list IMP-9-0-0-07")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "save":
        if len(sys.argv) < 4:
            print("❌ Usage: python baseline_manager.py save <item_id> <results_dir> [description]")
            sys.exit(1)
        
        item_id = sys.argv[2]
        results_dir = Path(sys.argv[3])
        description = sys.argv[4] if len(sys.argv) > 4 else None
        
        try:
            baseline_path = save_baseline(item_id, results_dir, description)
            print(f"\n✅ Baseline saved successfully")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    elif command == "load":
        if len(sys.argv) < 3:
            print("❌ Usage: python baseline_manager.py load <item_id>")
            sys.exit(1)
        
        item_id = sys.argv[2]
        
        baseline = load_baseline(item_id)
        if baseline:
            print(f"\n✅ Baseline loaded")
            print(json.dumps(baseline["summary"], indent=2))
        else:
            print(f"\n❌ No baseline found for {item_id}")
    
    elif command == "list":
        if len(sys.argv) < 3:
            print("❌ Usage: python baseline_manager.py list <item_id>")
            sys.exit(1)
        
        item_id = sys.argv[2]
        
        manager = BaselineManager(item_id)
        manager.list_baseline_history()
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: save, load, list")
        sys.exit(1)
