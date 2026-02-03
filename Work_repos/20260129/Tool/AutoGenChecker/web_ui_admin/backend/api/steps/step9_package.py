"""
Step 9: Package & Report API.

Package checker artifacts and generate report.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import traceback
from datetime import datetime

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify router is working"""
    return {"status": "ok", "message": "Step 9 router is working!"}


@router.post("/package-debug")
async def package_debug(request: Request):
    """Debug endpoint to see raw request"""
    body = await request.json()
    print(f"[DEBUG] Raw request body: {body}")
    print(f"[DEBUG] Body type: {type(body)}")
    for key, value in body.items():
        print(f"[DEBUG]   {key}: {type(value).__name__} = {str(value)[:100]}")
    return {"status": "debug", "received": body}


class PackageRequest(BaseModel):
    """Request model for packaging"""
    module: Optional[str] = ""
    item_id: Optional[str] = ""
    code: Optional[str] = ""
    readme: Optional[str] = ""
    config: Optional[Any] = None
    file_analysis: Optional[Any] = None


class PackageResponse(BaseModel):
    """Response model for packaging"""
    status: str
    package_path: Optional[str] = None
    artifacts: Optional[Dict[str, Any]] = None  # Can contain strings or lists
    report: Optional[str] = None
    error: Optional[str] = None


@router.post("/package", response_model=PackageResponse)
async def package_checker(request: PackageRequest):
    """
    Package checker artifacts and generate report.
    
    Creates:
    - Checker code file
    - README file
    - Configuration file
    - Generation report
    
    Returns:
        PackageResponse with package details
    """
    print(f"[DEBUG] Step 9 package request received")
    print(f"[DEBUG] module: {request.module}")
    print(f"[DEBUG] item_id: {request.item_id}")
    print(f"[DEBUG] code length: {len(request.code) if request.code else 0}")
    print(f"[DEBUG] readme length: {len(request.readme) if request.readme else 0}")
    
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        from utils.paths import discover_project_paths
        from pathlib import Path
        import shutil
        
        # Create agent
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            verbose=False,
            interactive=False
        )
        
        # Get paths - new structure: release/{item_id}/
        paths = discover_project_paths()
        release_dir = paths.workspace_root / "Check_modules" / request.module / "release" / request.item_id
        
        # Ensure directory exists
        release_dir.mkdir(parents=True, exist_ok=True)
        
        # Save checker code: {item_id}.py
        code_file = release_dir / f"{request.item_id}.py"
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(request.code)
        
        # Save README: {item_id}_README.md
        readme_file = release_dir / f"{request.item_id}_README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(request.readme)
        
        # Save YAML config: {item_id}.yaml
        yaml_file = None
        if request.config:
            import yaml
            yaml_file = release_dir / f"{request.item_id}.yaml"
            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(request.config, f, default_flow_style=False, allow_unicode=True)
        
        # Copy input files from config.input_files directly to release/{item_id}/
        copied_input_files = []
        if request.config and request.config.get('input_files'):
            for input_file_path in request.config['input_files']:
                input_path_str = str(input_file_path)
                
                # Replace ${CHECKLIST_ROOT} with workspace root
                if '${CHECKLIST_ROOT}' in input_path_str:
                    input_path_str = input_path_str.replace('${CHECKLIST_ROOT}', str(paths.workspace_root))
                
                input_path = Path(input_path_str)
                
                # If relative path, resolve from workspace root
                if not input_path.is_absolute():
                    input_path = paths.workspace_root / input_path_str
                
                if input_path.exists() and input_path.is_file():
                    # Copy directly to release/{item_id}/ without input_files subdirectory
                    dest_file = release_dir / input_path.name
                    shutil.copy2(input_path, dest_file)
                    copied_input_files.append(str(dest_file))
                    print(f"[DEBUG] Copied input file: {input_path.name}")
        
        # Generate report
        report = _generate_report(
            item_id=request.item_id,
            module=request.module,
            code_lines=len(request.code.split('\n')),
            readme_lines=len(request.readme.split('\n'))
        )
        
        artifacts = {
            'code': str(code_file),
            'readme': str(readme_file),
            'yaml': str(yaml_file) if yaml_file else None,
            'input_files': copied_input_files,
        }
        
        return PackageResponse(
            status="success",
            package_path=str(release_dir),
            artifacts=artifacts,
            report=report
        )
        
    except Exception as e:
        error_msg = f"Package failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return PackageResponse(
            status="error",
            error=error_msg
        )


class ViewFileRequest(BaseModel):
    """Request model for viewing file content"""
    file_path: str


class ViewFileResponse(BaseModel):
    """Response model for viewing file content"""
    status: str
    content: Optional[str] = None
    file_name: Optional[str] = None
    error: Optional[str] = None


@router.post("/view-file", response_model=ViewFileResponse)
async def view_file(request: ViewFileRequest):
    """
    Read and return file content.
    """
    try:
        from pathlib import Path
        
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            return ViewFileResponse(
                status="error",
                error=f"File not found: {request.file_path}"
            )
        
        if not file_path.is_file():
            return ViewFileResponse(
                status="error",
                error=f"Not a file: {request.file_path}"
            )
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 for binary-like files
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        return ViewFileResponse(
            status="success",
            content=content,
            file_name=file_path.name
        )
        
    except Exception as e:
        return ViewFileResponse(
            status="error",
            error=str(e)
        )


class GitUploadRequest(BaseModel):
    """Request model for git upload"""
    module: str
    item_id: str
    branch_name: Optional[str] = None
    commit_message: Optional[str] = None
    input_files: Optional[list] = None  # List of input file paths from config


class GitUploadResponse(BaseModel):
    """Response model for git upload"""
    status: str
    branch: Optional[str] = None
    commit: Optional[str] = None
    files_uploaded: Optional[list] = None
    error: Optional[str] = None


@router.post("/git-upload", response_model=GitUploadResponse)
async def upload_to_git(request: GitUploadRequest):
    """
    Upload release/{item_id}/ directory to git branch.
    
    Creates a new branch (or uses existing), commits the directory, and pushes to remote.
    
    Returns:
        GitUploadResponse with upload details
    """
    print(f"[DEBUG] Git upload request received")
    print(f"[DEBUG] module: {request.module}")
    print(f"[DEBUG] item_id: {request.item_id}")
    print(f"[DEBUG] branch_name: {request.branch_name}")
    
    try:
        from utils.paths import discover_project_paths
        from pathlib import Path
        import subprocess
        
        # Get paths - upload entire release/{item_id}/ directory
        paths = discover_project_paths()
        release_dir = paths.workspace_root / "Check_modules" / request.module / "release" / request.item_id
        
        if not release_dir.exists():
            raise Exception(f"Release directory not found: {release_dir}. Please run Package first.")
        
        # Determine branch name
        branch_name = request.branch_name or f"checker-{request.module}-{request.item_id}"
        
        # Determine commit message
        commit_msg = request.commit_message or f"Add checker for {request.module}/{request.item_id}"
        
        # Collect all files in release/{item_id}/ directory
        files_to_upload = []
        for file_path in release_dir.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(paths.workspace_root)
                files_to_upload.append(str(rel_path))
                print(f"[DEBUG] Added file: {rel_path}")
        
        if not files_to_upload:
            raise Exception("No files found to upload in release directory")
        
        # Change to workspace root
        original_cwd = Path.cwd()
        import os
        os.chdir(paths.workspace_root)
        
        try:
            # Get current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # Create and checkout new branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                capture_output=True,
                text=True,
                check=False  # May fail if branch exists
            )
            
            # If branch exists, just checkout
            subprocess.run(
                ['git', 'checkout', branch_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Add files
            for file_path in files_to_upload:
                subprocess.run(
                    ['git', 'add', file_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            # Commit
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                text=True,
                check=False  # May fail if nothing to commit
            )
            
            commit_hash = None
            if result.returncode == 0:
                # Get commit hash
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_hash = result.stdout.strip()[:8]
            
            # Push to remote
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch_name],
                capture_output=True,
                text=True,
                check=False  # May fail if no remote
            )
            
            # Return to original branch
            subprocess.run(
                ['git', 'checkout', current_branch],
                capture_output=True,
                text=True,
                check=False
            )
            
            return GitUploadResponse(
                status="success",
                branch=branch_name,
                commit=commit_hash,
                files_uploaded=files_to_upload
            )
            
        finally:
            os.chdir(original_cwd)
    
    except Exception as e:
        error_msg = f"Git upload failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return GitUploadResponse(
            status="error",
            error=error_msg
        )


def _generate_report(
    item_id: str,
    module: str,
    code_lines: int,
    readme_lines: int
) -> str:
    """Generate completion report"""
    
    now = datetime.now()
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          CHECKER GENERATION REPORT                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 Project Information
─────────────────────────────────────────────────────────────────────────────
  Item ID:          {item_id}
  Module:           {module}
  Generated:        {now.strftime('%Y-%m-%d %H:%M:%S')}

📊 Artifacts Generated
─────────────────────────────────────────────────────────────────────────────
  ✓ Checker Code:   {code_lines} lines
  ✓ README:         {readme_lines} lines
  ✓ Configuration:  YAML

🎯 Workflow Completed
─────────────────────────────────────────────────────────────────────────────
  Step 1: Configuration       ✓
  Step 2: File Analysis        ✓
  Step 3: README Generation    ✓
  Step 4: README Review        ✓
  Step 5: Code Generation      ✓
  Step 6: Self-Check & Fix     ✓
  Step 7: Interactive Testing  ✓
  Step 8: Final Review         ✓
  Step 9: Package & Report     ✓

✅ Checker development completed successfully!

Next Steps:
  1. Review generated code in checker directory
  2. Run manual tests if needed
  3. Deploy to production when ready

╔══════════════════════════════════════════════════════════════════════════════╗
║                        Generated by AutoGenChecker                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    return report
