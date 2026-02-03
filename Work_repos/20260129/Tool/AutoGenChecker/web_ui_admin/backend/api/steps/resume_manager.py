"""
Resume Manager - Load cached data for resume functionality.

This module provides resume capabilities matching CLI's _load_cached_data()
in workflow/intelligent_agent.py.

Cached data locations:
- Config: Check_modules/{module}/inputs/items/{item_id}.yaml
- File Analysis: Check_modules/{module}/scripts/doc/{item_id}_file_analysis.json
- README: Check_modules/{module}/scripts/doc/{item_id}_README.md
- Code: Check_modules/{module}/scripts/checker/{item_id}.py
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import yaml

# Get CHECKLIST root directory
CHECKLIST_ROOT = Path(os.environ.get(
    "CHECKLIST_ROOT",
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent / "CHECKLIST"
))


class ResumeManager:
    """Manager for loading cached workflow data."""
    
    def __init__(self, module: str, item_id: str):
        self.module = module
        self.item_id = item_id
        self.workspace_root = CHECKLIST_ROOT
    
    def get_paths(self) -> Dict[str, Path]:
        """Get all relevant file paths."""
        module_dir = self.workspace_root / "Check_modules" / self.module
        return {
            'config': module_dir / "inputs" / "items" / f"{self.item_id}.yaml",
            'file_analysis': module_dir / "scripts" / "doc" / f"{self.item_id}_file_analysis.json",
            'readme': module_dir / "scripts" / "doc" / f"{self.item_id}_README.md",
            'readme_backup': module_dir / "scripts" / "doc" / f"{self.item_id}_README.md.backup",
            'code': module_dir / "scripts" / "checker" / f"{self.item_id}.py",
            'code_backup': module_dir / "scripts" / "checker" / f"{self.item_id}.py.backup",
            'hints': self.workspace_root / "Work" / "phase-1-dev" / self.module / "hints.txt",
        }
    
    def get_file_info(self, path: Path) -> Optional[Dict[str, Any]]:
        """Get file information if exists."""
        if not path.exists():
            return None
        
        stat = path.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        return {
            'exists': True,
            'path': str(path),
            'size': stat.st_size,
            'modified_time': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
            'modified_timestamp': stat.st_mtime,
        }
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load YAML config file."""
        paths = self.get_paths()
        config_path = paths['config']
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return {
                'item_id': self.item_id,
                'module': self.module,
                'description': config_data.get('description', 'TBD'),
                'input_files': config_data.get('input_files', []),
                'requirements': config_data.get('requirements', {}),
                'waivers': config_data.get('waivers', {}),
                'config_file': str(config_path),
                'file_info': self.get_file_info(config_path),
            }
        except Exception as e:
            print(f"[ResumeManager] Failed to load config: {e}")
            return None
    
    def load_file_analysis(self) -> Optional[List[Dict[str, Any]]]:
        """Load file analysis JSON."""
        paths = self.get_paths()
        analysis_path = paths['file_analysis']
        
        if not analysis_path.exists():
            return None
        
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            print(f"[ResumeManager] Failed to load file_analysis: {e}")
            return None
    
    def load_readme(self) -> Optional[Dict[str, Any]]:
        """Load README file."""
        paths = self.get_paths()
        readme_path = paths['readme']
        
        if not readme_path.exists():
            return None
        
        try:
            content = readme_path.read_text(encoding='utf-8')
            file_info = self.get_file_info(readme_path)
            
            # Check if backup exists
            backup_info = self.get_file_info(paths['readme_backup'])
            
            return {
                'content': content,
                'file_info': file_info,
                'has_backup': backup_info is not None,
                'backup_info': backup_info,
            }
        except Exception as e:
            print(f"[ResumeManager] Failed to load README: {e}")
            return None
    
    def load_code(self) -> Optional[Dict[str, Any]]:
        """Load checker code file."""
        paths = self.get_paths()
        code_path = paths['code']
        
        if not code_path.exists():
            return None
        
        try:
            content = code_path.read_text(encoding='utf-8')
            file_info = self.get_file_info(code_path)
            
            # Check if backup exists
            backup_info = self.get_file_info(paths['code_backup'])
            
            return {
                'content': content,
                'file_info': file_info,
                'has_backup': backup_info is not None,
                'backup_info': backup_info,
                'lines': len(content.split('\n')),
            }
        except Exception as e:
            print(f"[ResumeManager] Failed to load code: {e}")
            return None
    
    def load_hints(self) -> Optional[str]:
        """Load hints file."""
        paths = self.get_paths()
        hints_path = paths['hints']
        
        if not hints_path.exists():
            return None
        
        try:
            return hints_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"[ResumeManager] Failed to load hints: {e}")
            return None
    
    def save_file_analysis(self, data: List[Dict[str, Any]]) -> str:
        """Save file analysis to JSON file."""
        paths = self.get_paths()
        analysis_path = paths['file_analysis']
        analysis_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[ResumeManager] 💾 Saved file_analysis to {analysis_path}")
        return str(analysis_path)
    
    def get_resume_status(self) -> Dict[str, Any]:
        """
        Get complete resume status for all steps.
        
        Returns dict indicating which steps can be resumed from:
        - Step 1: Always available (config selection)
        - Step 2: Requires config
        - Step 3: Requires config + file_analysis
        - Step 4: Requires README
        - Step 5: Requires README
        - Step 6+: Requires code
        """
        paths = self.get_paths()
        
        config_info = self.get_file_info(paths['config'])
        analysis_info = self.get_file_info(paths['file_analysis'])
        readme_info = self.get_file_info(paths['readme'])
        code_info = self.get_file_info(paths['code'])
        
        # Determine available resume points
        can_resume = {
            1: True,  # Always can start from step 1
            2: config_info is not None,
            3: config_info is not None,  # Can generate README with just config
            4: readme_info is not None,
            5: readme_info is not None,
            6: code_info is not None,
            7: code_info is not None,
            8: code_info is not None,
            9: code_info is not None,
        }
        
        # Suggest the latest possible resume step
        latest_resume_step = 1
        if code_info:
            latest_resume_step = 6  # Can resume from self-check
        elif readme_info:
            latest_resume_step = 5  # Can resume from code generation
        elif analysis_info:
            latest_resume_step = 3  # Can resume from README generation
        elif config_info:
            latest_resume_step = 2  # Can resume from file analysis
        
        return {
            'module': self.module,
            'item_id': self.item_id,
            'files': {
                'config': config_info,
                'file_analysis': analysis_info,
                'readme': readme_info,
                'code': code_info,
            },
            'can_resume': can_resume,
            'suggested_resume_step': latest_resume_step,
            'message': self._get_resume_message(latest_resume_step, config_info, analysis_info, readme_info, code_info),
        }
    
    def _get_resume_message(self, step: int, config, analysis, readme, code) -> str:
        """Generate human-readable resume message."""
        if step == 1:
            return "No previous work found. Start from Step 1."
        
        msgs = []
        if config:
            msgs.append(f"✅ Config found")
        if analysis:
            msgs.append(f"✅ File analysis found")
        if readme:
            msgs.append(f"✅ README found ({readme['modified_time']})")
        if code:
            msgs.append(f"✅ Code found ({code['modified_time']})")
        
        msgs.append(f"📍 Can resume from Step {step}")
        return " | ".join(msgs)


# Singleton-like access
def get_resume_manager(module: str, item_id: str) -> ResumeManager:
    """Get a ResumeManager instance."""
    return ResumeManager(module, item_id)
