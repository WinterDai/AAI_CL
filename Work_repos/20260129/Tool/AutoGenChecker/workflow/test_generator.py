"""
Test Configuration Generator for Comprehensive Checker Testing.

Generates 6 types of test YAML configurations:
1. type1_na: Type 1 无数据
2. type1_w0: Type 1 waivers.value=0
3. type2: Type 2 标准检查
4. type3: Type 3 with waivers
5. type4: Type 4 all items fail
6. type4_all: Type 4 mix (some PASS, some WAIVED)

Storage: Work/test_configs/{item_id}/
"""

from pathlib import Path
from typing import Dict, List, Any
import yaml
from datetime import datetime


class TestConfigGenerator:
    """Generate comprehensive test configurations for a checker."""
    
    # Test type templates
    TEST_TYPES = {
        "type1_na": {
            "description": "Type 1 - No data (input file empty/missing)",
            "template": {
                "requirements": {"value": 1},
                "waivers": {"value": "N/A", "waive_items": []},
            }
        },
        "type1_w0": {
            "description": "Type 1 - waivers.value=0 (force PASS mode)",
            "template": {
                "requirements": {"value": 1},
                "waivers": {
                    "value": 0,
                    "waive_items": [
                        "EXPLANATION: This is informational check - violations expected and acceptable"
                    ]
                },
            }
        },
        "type2": {
            "description": "Type 2 - Pattern value check",
            "template": {
                "requirements": {
                    "value": 2,  # Must match len(pattern_items)
                    "pattern_items": ["PATTERN_1", "PATTERN_2"]
                },
                "waivers": {"value": "N/A", "waive_items": []},
            }
        },
        "type3": {
            "description": "Type 3 - Pattern check with waivers",
            "template": {
                "requirements": {
                    "value": 2,
                    "pattern_items": ["PATTERN_1", "PATTERN_2"]
                },
                "waivers": {
                    "value": 1,
                    "waive_items": [
                        {"name": "PATTERN_1", "reason": "Waived per design review"}
                    ]
                },
            }
        },
        "type4": {
            "description": "Type 4 - All items fail (no waivers)",
            "template": {
                "requirements": {
                    "value": 2,
                    "pattern_items": ["PATTERN_1", "PATTERN_2"]
                },
                "waivers": {"value": "N/A", "waive_items": []},
            }
        },
        "type4_all": {
            "description": "Type 4 - Mix (some PASS, some WAIVED)",
            "template": {
                "requirements": {
                    "value": 3,
                    "pattern_items": ["PATTERN_1", "PATTERN_2", "PATTERN_3"]
                },
                "waivers": {
                    "value": 1,
                    "waive_items": [
                        {"name": "PATTERN_2", "reason": "Waived - known issue"}
                    ]
                },
            }
        },
    }
    
    def __init__(self, item_id: str, module: str, base_config: Dict[str, Any]):
        """
        Initialize test generator.
        
        Args:
            item_id: Checker ID (e.g., "IMP-9-0-0-07")
            module: Module name (e.g., "9.0_RC_EXTRACTION_CHECK")
            base_config: Base configuration loaded from item YAML
        """
        self.item_id = item_id
        self.module = module
        self.base_config = base_config
        
        # Setup test config directory
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        self.test_config_dir = paths.workspace_root / "Work" / "test_configs" / item_id
        self.test_config_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_test_configs(self) -> Dict[str, Path]:
        """
        Generate all 6 test configurations.
        
        Returns:
            Dict mapping test type to config file path
        """
        configs = {}
        
        print(f"\n📋 Generating test configurations for {self.item_id}...")
        
        for test_type, test_info in self.TEST_TYPES.items():
            config_path = self._generate_single_config(test_type, test_info)
            configs[test_type] = config_path
            print(f"  ✅ {test_type}: {config_path.name}")
        
        # Generate manifest
        manifest_path = self._generate_manifest(configs)
        print(f"  📄 manifest.json: {manifest_path.name}")
        
        return configs
    
    def _generate_single_config(self, test_type: str, test_info: Dict[str, Any]) -> Path:
        """Generate a single test configuration file."""
        # Start with base config
        config = {
            self.item_id: {
                "description": self.base_config.get("description", ""),
                "input_files": self.base_config.get("input_files", []),
            }
        }
        
        # Merge template
        template = test_info["template"]
        config[self.item_id].update(template)
        
        # Customize pattern_items based on actual config
        if "pattern_items" in template.get("requirements", {}):
            # Try to extract real patterns from base config
            real_patterns = self._extract_real_patterns()
            if real_patterns:
                config[self.item_id]["requirements"]["pattern_items"] = real_patterns[:3]
                # Update value to match pattern count
                config[self.item_id]["requirements"]["value"] = len(real_patterns[:3])
                
                # Update waivers for type3/type4_all
                if test_type in ["type3", "type4_all"]:
                    waive_items = config[self.item_id]["waivers"]["waive_items"]
                    if waive_items:
                        # Use first real pattern for waiver
                        waive_items[0]["name"] = real_patterns[0]
        
        # Save to file
        config_file = self.test_config_dir / f"{test_type}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return config_file
    
    def _extract_real_patterns(self) -> List[str]:
        """
        Extract real patterns from base configuration.
        
        Returns:
            List of pattern strings, or generic patterns if not found
        """
        # Check if base config has pattern_items
        requirements = self.base_config.get("requirements", {})
        if "pattern_items" in requirements:
            patterns = requirements["pattern_items"]
            if isinstance(patterns, list) and patterns:
                return patterns
        
        # Return generic patterns
        return ["PATTERN_1", "PATTERN_2", "PATTERN_3"]
    
    def _generate_manifest(self, configs: Dict[str, Path]) -> Path:
        """Generate manifest.json with test metadata."""
        manifest = {
            "item_id": self.item_id,
            "module": self.module,
            "generated_at": datetime.now().isoformat(),
            "test_types": {},
        }
        
        for test_type, config_path in configs.items():
            test_info = self.TEST_TYPES[test_type]
            manifest["test_types"][test_type] = {
                "description": test_info["description"],
                "config_file": config_path.name,
                "expected_status": self._infer_expected_status(test_type),
            }
        
        manifest_path = self.test_config_dir / "manifest.json"
        import json
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path
    
    def _infer_expected_status(self, test_type: str) -> str:
        """Infer expected test status for each type."""
        if test_type == "type1_na":
            return "PASS"  # No data usually means PASS
        elif test_type == "type1_w0":
            return "PASS"  # Forced PASS mode
        elif test_type == "type2":
            return "DEPENDS"  # Can be PASS or FAIL
        elif test_type == "type3":
            return "DEPENDS"  # PASS with waivers
        elif test_type == "type4":
            return "ERROR"  # All items fail
        elif test_type == "type4_all":
            return "MIX"  # Some PASS, some WAIVED, some ERROR
        
        return "UNKNOWN"


def generate_test_configs(item_id: str, module: str) -> Dict[str, Path]:
    """
    Convenience function to generate test configs for a checker.
    
    Args:
        item_id: Checker ID
        module: Module name
    
    Returns:
        Dict mapping test type to config file path
    """
    # Load base config
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    paths = discover_project_paths()
    config_file = (
        paths.workspace_root / 
        "Check_modules" / 
        module / 
        "inputs" / 
        "items" / 
        f"{item_id}.yaml"
    )
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        base_config_dict = yaml.safe_load(f)
    
    # Extract item config
    base_config = base_config_dict.get(item_id, {})
    
    # Generate configs
    generator = TestConfigGenerator(item_id, module, base_config)
    return generator.generate_all_test_configs()


if __name__ == "__main__":
    # Test generation
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_generator.py <item_id> <module>")
        print("Example: python test_generator.py IMP-9-0-0-07 9.0_RC_EXTRACTION_CHECK")
        sys.exit(1)
    
    item_id = sys.argv[1]
    module = sys.argv[2]
    
    print(f"\nTest Config Generator")
    print(f"Item: {item_id}")
    print(f"Module: {module}")
    
    try:
        configs = generate_test_configs(item_id, module)
        print(f"\n✅ Generated {len(configs)} test configurations")
        print(f"📁 Location: Work/test_configs/{item_id}/")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
