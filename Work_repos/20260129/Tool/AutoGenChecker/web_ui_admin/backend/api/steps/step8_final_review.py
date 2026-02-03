"""
Step 8: Final Review API.

Handle final review actions: Test, Modify, Optimize, Verify, Reset, Finalize, Quit.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback

router = APIRouter()


class FinalReviewRequest(BaseModel):
    """Request model for final review"""
    module: str
    item_id: str
    code: str
    config: dict
    file_analysis: Optional[dict] = None
    readme: Optional[str] = None
    action: str  # 't', 'm', 'o', 'v', 'r', 'f', 'q'
    modified_code: Optional[str] = None


class FinalReviewResponse(BaseModel):
    """Response model for final review"""
    status: str
    action: str
    next_step: Optional[str] = None
    code: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


@router.post("/review", response_model=FinalReviewResponse)
async def final_review(request: FinalReviewRequest):
    """
    Handle final review action.
    
    Actions:
    - T: Test - Run all tests
    - M: Modify - Save modified code
    - O: Optimize - AI optimize code
    - V: Verify - Re-run validation
    - R: Reset - Back to Step 5 (regenerate)
    - F: Finalize - Accept and proceed to Step 9
    - Q: Quit - Exit without saving
    
    Returns:
        FinalReviewResponse with action result
    """
    try:
        action = request.action.lower()
        
        if action == 't':
            # Test - redirect to Step 7
            return FinalReviewResponse(
                status="success",
                action="test",
                next_step="step7",
                message="Redirecting to testing..."
            )
            
        elif action == 'm':
            # Modify - save modified code
            if not request.modified_code:
                return FinalReviewResponse(
                    status="error",
                    action="modify",
                    error="No modified code provided"
                )
            
            return FinalReviewResponse(
                status="success",
                action="modify",
                code=request.modified_code,
                message="Code saved successfully"
            )
            
        elif action == 'o':
            # Optimize - AI optimize code using the code generator
            try:
                from llm_clients.client_factory import LLMClientFactory
                
                client = LLMClientFactory.create()
                
                prompt = f"""请优化以下Python代码，使其更简洁、高效、可读性更好。
保持代码功能不变，但可以：
1. 改进代码结构和命名
2. 添加缺失的注释
3. 优化算法效率
4. 修复潜在问题

原代码:
```python
{request.code}
```

请直接返回优化后的完整Python代码，不要包含任何解释或markdown标记。
"""
                
                response = client.chat_with_codes(
                    prompt=prompt,
                    system_prompt="You are a Python code optimization expert. Return only the optimized code without any markdown formatting or explanations."
                )
                
                optimized_code = response.strip()
                
                # Clean up any markdown code blocks if present
                if optimized_code.startswith("```python"):
                    optimized_code = optimized_code[9:]
                if optimized_code.startswith("```"):
                    optimized_code = optimized_code[3:]
                if optimized_code.endswith("```"):
                    optimized_code = optimized_code[:-3]
                optimized_code = optimized_code.strip()
                
                return FinalReviewResponse(
                    status="success",
                    action="optimize",
                    code=optimized_code,
                    message="Code optimized successfully"
                )
            except Exception as e:
                return FinalReviewResponse(
                    status="error",
                    action="optimize",
                    error=f"Optimization failed: {str(e)}"
                )
            
        elif action == 'v':
            # Verify - re-run validation using quick_validate_code
            try:
                from workflow.intelligent_agent import IntelligentCheckerAgent
                
                agent = IntelligentCheckerAgent(
                    item_id=request.item_id,
                    module=request.module,
                    verbose=False,
                    interactive=False
                )
                
                validation_result = agent._quick_validate_code(request.code)
                
                issue_count = len(validation_result.get('syntax_errors', [])) + len(validation_result.get('known_issues', []))
                
                if validation_result.get('has_errors'):
                    message = f"Validation found {issue_count} issue(s)"
                    if validation_result.get('syntax_errors'):
                        message += f" - Syntax errors: {validation_result['syntax_errors']}"
                    if validation_result.get('known_issues'):
                        message += f" - Known issues: {len(validation_result['known_issues'])}"
                else:
                    message = "Validation passed - no issues found"
                
                return FinalReviewResponse(
                    status="success",
                    action="verify",
                    message=message,
                    code=request.code
                )
            except Exception as e:
                return FinalReviewResponse(
                    status="error",
                    action="verify",
                    error=f"Validation failed: {str(e)}"
                )
            
        elif action == 'r':
            # Reset - back to Step 5
            return FinalReviewResponse(
                status="success",
                action="reset",
                next_step="step5",
                message="Resetting to code generation..."
            )
            
        elif action == 'f':
            # Finalize - proceed to Step 9
            return FinalReviewResponse(
                status="success",
                action="finalize",
                next_step="step9",
                code=request.code,
                message="Finalizing..."
            )
            
        elif action == 'q':
            # Quit - exit
            return FinalReviewResponse(
                status="success",
                action="quit",
                message="Exiting without saving"
            )
            
        else:
            return FinalReviewResponse(
                status="error",
                action=action,
                error=f"Unknown action: {action}"
            )
        
    except Exception as e:
        error_msg = f"Final review failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        traceback.print_exc()
        
        return FinalReviewResponse(
            status="error",
            action=request.action,
            error=error_msg
        )
