"""
Step 6: Self-Check & Fix API.

Validate generated code and auto-fix issues.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Union
import traceback
import json
import asyncio

router = APIRouter()


class SelfCheckRequest(BaseModel):
    """Request model for self-check"""
    module: str
    item_id: str
    code: str
    config: Optional[dict] = None
    file_analysis: Optional[Union[list, dict]] = None
    readme: Optional[str] = ""
    max_fix_attempts: int = 3
    llm_provider: str = 'jedai'
    llm_model: str = 'claude-sonnet-4-5'


class SelfCheckResponse(BaseModel):
    """Response model for self-check"""
    status: str
    fixed_code: Optional[str] = None
    has_issues: bool = False
    has_warnings: bool = False
    critical_count: int = 0
    warning_count: int = 0
    fix_attempts: int = 0
    issues: list[dict] = []
    check_log: list[str] = []  # Detailed check log like CLI
    error: Optional[str] = None


async def generate_check_stream(request: SelfCheckRequest):
    """
    Generator for streaming check progress via SSE.
    """
    try:
        # Import IntelligentCheckerAgent
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        # Send initial log
        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '[Step 6/9] 🔍 Self-Check & Fix'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
        await asyncio.sleep(0.05)
        
        # Create agent instance
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '  🤖 Initializing checker agent...'})}\n\n"
        await asyncio.sleep(0.05)
        
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            verbose=False,
            interactive=False,
            max_fix_attempts=request.max_fix_attempts
        )
        
        yield f"data: {json.dumps({'type': 'log', 'message': '  ✅ Agent initialized'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        await asyncio.sleep(0.05)
        
        # Log check categories being run
        yield f"data: {json.dumps({'type': 'log', 'message': '  Running checks:'})}\n\n"
        await asyncio.sleep(0.02)
        
        checks = [
            "Known issues (CodeValidator)",
            "Syntax validation",
            "Template compliance",
            "Required methods",
            "Import validation",
            "Waiver tag rules",
            "Type 1/2 reason usage",
            "Regex raw string check",
            "Runtime validation",
            "build_complete_output() parameters"
        ]
        
        for check in checks:
            yield f"data: {json.dumps({'type': 'log', 'message': f'    ⏳ {check}...'})}\n\n"
            await asyncio.sleep(0.1)
        
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '  🔧 Running self-check and auto-fix...'})}\n\n"
        await asyncio.sleep(0.05)
        
        # Run self-check and fix
        fixed_code, check_results = agent._self_check_and_fix(
            code=request.code,
            config=request.config,
            file_analysis=request.file_analysis,
            readme=request.readme
        )
        
        # Process results
        issues = check_results.get('issues', [])
        fix_attempts = check_results.get('fix_attempts', 0)
        critical_count = check_results.get('critical_count', 0)
        warning_count = check_results.get('warning_count', 0)
        has_issues = check_results.get('has_issues', False)
        has_warnings = check_results.get('has_warnings', False)
        
        # Mark checks as done
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        for check in checks:
            yield f"data: {json.dumps({'type': 'log', 'message': f'    ✓ {check}'})}\n\n"
            await asyncio.sleep(0.02)
        
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        await asyncio.sleep(0.05)
        
        # Log issue details
        if issues:
            critical_issues = [i for i in issues if i.get('severity') == 'critical']
            warning_issues = [i for i in issues if i.get('severity') != 'critical']
            
            if critical_issues:
                yield f"data: {json.dumps({'type': 'log', 'message': f'  ❌ Found {len(critical_issues)} CRITICAL issue(s):'})}\n\n"
                await asyncio.sleep(0.05)
                for idx, issue in enumerate(critical_issues, 1):
                    msg = issue.get('message', 'Unknown issue')[:100]
                    issue_type = issue.get('type', 'UNKNOWN')
                    log_msg = f'    {idx}. [{issue_type}] {msg}'
                    yield f"data: {json.dumps({'type': 'log', 'message': log_msg})}\n\n"
                    suggestion = issue.get('suggestion', '')
                    if suggestion:
                        hint_msg = f'       💡 {suggestion[:80]}'
                        yield f"data: {json.dumps({'type': 'log', 'message': hint_msg})}\n\n"
                    await asyncio.sleep(0.03)
                yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
            
            if warning_issues:
                yield f"data: {json.dumps({'type': 'log', 'message': f'  ⚠️ Found {len(warning_issues)} WARNING(s):'})}\n\n"
                await asyncio.sleep(0.05)
                for idx, issue in enumerate(warning_issues[:5], 1):
                    msg = issue.get('message', 'Unknown warning')[:100]
                    issue_type = issue.get('type', 'UNKNOWN')
                    log_msg = f'    {idx}. [{issue_type}] {msg}'
                    yield f"data: {json.dumps({'type': 'log', 'message': log_msg})}\n\n"
                    await asyncio.sleep(0.03)
                if len(warning_issues) > 5:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'    ... and {len(warning_issues) - 5} more warnings'})}\n\n"
                yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        
        # Log fix attempts
        if fix_attempts > 0:
            yield f"data: {json.dumps({'type': 'log', 'message': f'  🔧 Auto-fix attempts: {fix_attempts}'})}\n\n"
            await asyncio.sleep(0.05)
        
        # Final status
        if not has_issues and not has_warnings:
            if fix_attempts == 0:
                yield f"data: {json.dumps({'type': 'log', 'message': '  ✅ All checks passed on first try!'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'log', 'message': f'  ✅ All checks passed after {fix_attempts} fix(es)'})}\n\n"
        elif not has_issues and has_warnings:
            yield f"data: {json.dumps({'type': 'log', 'message': f'  ✅ No critical issues! {warning_count} warning(s) noted.'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'log', 'message': f'  ❌ {critical_count} critical issue(s) remain after {fix_attempts} attempt(s)'})}\n\n"
        
        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '[Self-Check Complete]'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 60})}\n\n"
        await asyncio.sleep(0.05)
        
        # Send final result
        result = {
            'type': 'complete',
            'status': 'success',
            'fixed_code': fixed_code,
            'has_issues': has_issues,
            'has_warnings': has_warnings,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'fix_attempts': fix_attempts,
            'issues': issues
        }
        yield f"data: {json.dumps(result)}\n\n"
        
    except Exception as e:
        error_msg = f"Self-check failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        yield f"data: {json.dumps({'type': 'log', 'message': f'❌ Error: {error_msg}'})}\n\n"
        yield f"data: {json.dumps({'type': 'complete', 'status': 'error', 'error': error_msg})}\n\n"


@router.post("/check-and-fix-stream")
async def check_and_fix_stream(request: SelfCheckRequest):
    """
    Stream self-check progress via Server-Sent Events.
    
    Returns:
        StreamingResponse with SSE events
    """
    return StreamingResponse(
        generate_check_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/check-and-fix", response_model=SelfCheckResponse)
async def check_and_fix(request: SelfCheckRequest):
    """
    Run self-check and auto-fix on generated code.
    
    Checks include:
    - Syntax validation
    - Template compliance
    - Required methods presence
    - Import validation
    - Waiver tag rules
    - Runtime validation
    
    Returns:
        SelfCheckResponse with fixed code and issue details
    """
    try:
        # Import IntelligentCheckerAgent
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        # Create agent instance with JEDAI LLM (same as other steps)
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            verbose=False,
            interactive=False,
            max_fix_attempts=request.max_fix_attempts
        )
        
        # Build check log like CLI does
        check_log = [
            "─" * 60,
            "[Step 6/9] 🔍 Self-Check & Fix",
            "─" * 60,
        ]
        
        # Run self-check and fix
        fixed_code, check_results = agent._self_check_and_fix(
            code=request.code,
            config=request.config,
            file_analysis=request.file_analysis,
            readme=request.readme
        )
        
        # Add detailed check results to log
        issues = check_results.get('issues', [])
        fix_attempts = check_results.get('fix_attempts', 0)
        critical_count = check_results.get('critical_count', 0)
        warning_count = check_results.get('warning_count', 0)
        has_issues = check_results.get('has_issues', False)
        has_warnings = check_results.get('has_warnings', False)
        
        # Log check categories run
        check_log.append("  Running checks:")
        check_log.append("    ✓ Known issues (CodeValidator)")
        check_log.append("    ✓ Syntax validation")
        check_log.append("    ✓ Template compliance")
        check_log.append("    ✓ Required methods")
        check_log.append("    ✓ Import validation")
        check_log.append("    ✓ Waiver tag rules")
        check_log.append("    ✓ Type 1/2 reason usage")
        check_log.append("    ✓ Regex raw string check")
        check_log.append("    ✓ Runtime validation")
        check_log.append("    ✓ build_complete_output() parameters")
        check_log.append("")
        
        # Log issue details
        if issues:
            critical_issues = [i for i in issues if i.get('severity') == 'critical']
            warning_issues = [i for i in issues if i.get('severity') != 'critical']
            
            if critical_issues:
                check_log.append(f"  ❌ Found {len(critical_issues)} CRITICAL issue(s):")
                for i, issue in enumerate(critical_issues, 1):
                    msg = issue.get('message', 'Unknown issue')[:100]
                    check_log.append(f"    {i}. [{issue.get('type', 'UNKNOWN')}] {msg}")
                    if issue.get('suggestion'):
                        check_log.append(f"       💡 {issue['suggestion'][:80]}")
                check_log.append("")
            
            if warning_issues:
                check_log.append(f"  ⚠️ Found {len(warning_issues)} WARNING(s):")
                for i, issue in enumerate(warning_issues[:5], 1):  # Show first 5 warnings
                    msg = issue.get('message', 'Unknown warning')[:100]
                    check_log.append(f"    {i}. [{issue.get('type', 'UNKNOWN')}] {msg}")
                if len(warning_issues) > 5:
                    check_log.append(f"    ... and {len(warning_issues) - 5} more warnings")
                check_log.append("")
        
        # Log fix attempts
        if fix_attempts > 0:
            check_log.append(f"  🔧 Auto-fix attempts: {fix_attempts}")
        
        # Final status
        if not has_issues and not has_warnings:
            if fix_attempts == 0:
                check_log.append("  ✅ All checks passed on first try!")
            else:
                check_log.append(f"  ✅ All checks passed after {fix_attempts} fix(es)")
        elif not has_issues and has_warnings:
            check_log.append(f"  ✅ No critical issues! {warning_count} warning(s) noted.")
        else:
            check_log.append(f"  ❌ {critical_count} critical issue(s) remain after {fix_attempts} attempt(s)")
        
        check_log.append("")
        check_log.append("─" * 60)
        check_log.append("[Self-Check Complete]")
        check_log.append("─" * 60)
        
        return SelfCheckResponse(
            status="success",
            fixed_code=fixed_code,
            has_issues=has_issues,
            has_warnings=has_warnings,
            critical_count=critical_count,
            warning_count=warning_count,
            fix_attempts=fix_attempts,
            issues=issues,
            check_log=check_log
        )
        
    except Exception as e:
        error_msg = f"Self-check failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return SelfCheckResponse(
            status="error",
            error=error_msg
        )


@router.post("/manual-fix", response_model=SelfCheckResponse)
async def manual_fix(request: SelfCheckRequest):
    """
    Allow manual code fix before re-checking.
    
    Returns:
        SelfCheckResponse with validation results
    """
    try:
        from workflow.intelligent_agent import IntelligentCheckerAgent
        
        # Create agent instance with JEDAI LLM (same as other steps)
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            verbose=False,
            interactive=False
        )
        
        # Only run checks, no auto-fix
        issues = agent._run_all_checks(request.code, request.config)
        
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        warning_issues = [i for i in issues if i.get('severity') != 'critical']
        
        # Build check log
        check_log = [
            "─" * 60,
            "[Manual Validation] 🔍 Check Only (No Auto-Fix)",
            "─" * 60,
            "",
        ]
        
        check_log.append("  Running checks:")
        check_log.append("    ✓ Known issues (CodeValidator)")
        check_log.append("    ✓ Syntax validation")
        check_log.append("    ✓ Template compliance")
        check_log.append("    ✓ Required methods")
        check_log.append("    ✓ Import validation")
        check_log.append("    ✓ Waiver tag rules")
        check_log.append("    ✓ Type 1/2 reason usage")
        check_log.append("    ✓ Regex raw string check")
        check_log.append("    ✓ Runtime validation")
        check_log.append("    ✓ build_complete_output() parameters")
        check_log.append("")
        
        if critical_issues:
            check_log.append(f"  ❌ Found {len(critical_issues)} CRITICAL issue(s):")
            for i, issue in enumerate(critical_issues, 1):
                msg = issue.get('message', 'Unknown issue')[:100]
                check_log.append(f"    {i}. [{issue.get('type', 'UNKNOWN')}] {msg}")
                if issue.get('suggestion'):
                    check_log.append(f"       💡 {issue['suggestion'][:80]}")
            check_log.append("")
        
        if warning_issues:
            check_log.append(f"  ⚠️ Found {len(warning_issues)} WARNING(s):")
            for i, issue in enumerate(warning_issues[:5], 1):
                msg = issue.get('message', 'Unknown warning')[:100]
                check_log.append(f"    {i}. [{issue.get('type', 'UNKNOWN')}] {msg}")
            if len(warning_issues) > 5:
                check_log.append(f"    ... and {len(warning_issues) - 5} more warnings")
            check_log.append("")
        
        if not critical_issues and not warning_issues:
            check_log.append("  ✅ All checks passed!")
        elif not critical_issues:
            check_log.append(f"  ✅ No critical issues! {len(warning_issues)} warning(s) noted.")
        
        check_log.append("")
        check_log.append("─" * 60)
        check_log.append("[Manual Validation Complete]")
        check_log.append("─" * 60)
        
        return SelfCheckResponse(
            status="success",
            fixed_code=request.code,
            has_issues=len(critical_issues) > 0,
            has_warnings=len(warning_issues) > 0,
            critical_count=len(critical_issues),
            warning_count=len(warning_issues),
            fix_attempts=0,
            issues=issues,
            check_log=check_log
        )
        
    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return SelfCheckResponse(
            status="error",
            error=error_msg
        )
