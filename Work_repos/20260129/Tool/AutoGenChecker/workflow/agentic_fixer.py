"""
Agentic Fixer - AI Agent with Tool-Calling Capability for Code Fixing.

This module implements a true Agent pattern where AI can:
1. Search codebase for function/class definitions
2. Read files to understand context
3. Execute tests to verify fixes
4. Iterate until the fix is successful

Unlike simple single-shot AI calls, this agent can:
- Use tools to gather information
- Make multiple attempts
- Learn from failed fixes
- Verify its own solutions
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import glob
import fnmatch

# Setup import path
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))


class AgenticFixer:
    """
    AI Agent with tool-calling capability for fixing code.
    
    Tools available to the AI:
    - search_code: Search for patterns in codebase
    - read_file: Read file contents
    - run_test: Execute a test to verify fix
    - grep_function: Find function/method definitions
    
    The agent iterates until:
    - Fix is successful (test passes), or
    - Max iterations reached, or
    - User cancels
    """
    
    # Tool definitions for the AI
    TOOLS = [
        {
            "name": "search_code",
            "description": "Search for a pattern (regex or literal) in Python files. Returns matching lines with file paths and line numbers.",
            "parameters": {
                "pattern": "The pattern to search for (string or regex)",
                "is_regex": "Whether pattern is regex (default: false)",
                "file_pattern": "Glob pattern for files to search (default: **/*.py)"
            }
        },
        {
            "name": "read_file",
            "description": "Read contents of a file. Use this to understand API signatures, class definitions, etc.",
            "parameters": {
                "file_path": "Absolute or relative path to the file",
                "start_line": "Start line number (1-based, optional)",
                "end_line": "End line number (1-based, optional)"
            }
        },
        {
            "name": "find_definition",
            "description": "Find the definition of a function, class, or method in the codebase.",
            "parameters": {
                "name": "Name of the function/class/method to find",
                "type": "Type: 'function', 'class', or 'method' (default: any)"
            }
        },
        {
            "name": "submit_fix",
            "description": "Submit your fixed code. This will replace the current code and run tests.",
            "parameters": {
                "fixed_code": "The complete fixed Python code",
                "explanation": "Brief explanation of what you fixed"
            }
        }
    ]
    
    def __init__(
        self,
        work_dir: Path,
        llm_client: Any,
        max_iterations: int = 5,
        verbose: bool = True
    ):
        """
        Initialize the Agentic Fixer.
        
        Args:
            work_dir: Working directory (project root)
            llm_client: LLM client for AI calls
            max_iterations: Maximum fix attempts
            verbose: Whether to print progress
        """
        self.work_dir = Path(work_dir)
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Search paths for code
        self.search_paths = [
            self.work_dir,
            self.work_dir / "CHECKLIST",
            self.work_dir / "CHECKLIST" / "Check_modules" / "common",
        ]
        
        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []
    
    def fix_code(
        self,
        code: str,
        error_message: str,
        test_command: str,
        test_config_path: Optional[Path] = None,
        checker_path: Optional[Path] = None,
    ) -> Tuple[str, bool, str]:
        """
        Fix code using agentic approach with tool calling.
        
        Args:
            code: Current code that has errors
            error_message: Error message from failed test
            test_command: Command to run test
            test_config_path: Path to test config file
            checker_path: Path to checker file
            
        Returns:
            Tuple of (fixed_code, success, explanation)
        """
        if self.verbose:
            print("\n" + "="*70)
            print("🤖 AGENTIC FIXER: Starting intelligent fix process")
            print("="*70)
        
        # Initialize conversation
        self.conversation_history = []
        
        # Build initial prompt with tools
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_initial_prompt(code, error_message)
        
        current_code = code
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            if self.verbose:
                print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            
            # Call AI with tool support
            response = self._call_ai_with_tools(system_prompt, user_prompt)
            
            # Parse AI response for tool calls
            tool_calls, final_response = self._parse_tool_calls(response)
            
            if tool_calls:
                # Execute tools and gather results
                tool_results = []
                for tool_call in tool_calls:
                    if self.verbose:
                        print(f"🔧 Tool: {tool_call['name']}")
                    result = self._execute_tool(tool_call)
                    tool_results.append({
                        "tool": tool_call['name'],
                        "params": tool_call.get('parameters', {}),
                        "result": result
                    })
                    
                    # Check if this is a submit_fix call
                    if tool_call['name'] == 'submit_fix':
                        fixed_code = tool_call.get('parameters', {}).get('fixed_code', '')
                        explanation = tool_call.get('parameters', {}).get('explanation', '')
                        
                        if fixed_code:
                            # Run test to verify
                            if self.verbose:
                                print("🧪 Running test to verify fix...")
                            
                            success, test_output = self._run_test(
                                fixed_code, 
                                test_command, 
                                checker_path
                            )
                            
                            if success:
                                if self.verbose:
                                    print("✅ Fix successful!")
                                return fixed_code, True, explanation
                            else:
                                if self.verbose:
                                    print("❌ Test still failing, continuing...")
                                # Add failure to context for next iteration
                                user_prompt = self._build_retry_prompt(
                                    fixed_code, 
                                    test_output,
                                    explanation
                                )
                                current_code = fixed_code
                                continue
                
                # Add tool results to context
                user_prompt = self._build_tool_result_prompt(tool_results)
            
            else:
                # No tool calls - AI might have given up or needs guidance
                if self.verbose:
                    print("⚠️  AI didn't use any tools. Providing guidance...")
                user_prompt = self._build_guidance_prompt(current_code, error_message)
        
        # Max iterations reached
        if self.verbose:
            print(f"\n⚠️  Max iterations ({self.max_iterations}) reached")
        
        return current_code, False, "Max iterations reached without successful fix"
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tool definitions."""
        tools_json = json.dumps(self.TOOLS, indent=2)
        
        return f"""You are an expert Python debugging agent. You can use tools to investigate and fix code.

AVAILABLE TOOLS:
{tools_json}

HOW TO USE TOOLS:
When you need to use a tool, respond with a JSON block like this:
```tool_call
{{"name": "tool_name", "parameters": {{"param1": "value1"}}}}
```

You can make multiple tool calls in one response. Each tool call should be in its own ```tool_call``` block.

WORKFLOW:
1. Analyze the error message to understand what's wrong
2. Use search_code or find_definition to find relevant code in the codebase
3. Use read_file to understand API signatures, class structures, etc.
4. When you're confident about the fix, use submit_fix with the complete fixed code

IMPORTANT RULES:
1. ALWAYS search the codebase to understand the correct API before fixing
2. Don't guess parameter names - find the actual definition
3. When you submit_fix, include the COMPLETE code, not just the changed part
4. If your fix fails, analyze the new error and try again

COMMON ISSUES TO CHECK:
- Wrong parameter names (search for the actual function signature)
- Wrong data types (Dict[str, str] vs Dict[str, Dict])
- Missing imports
- Incorrect method calls"""
    
    def _build_initial_prompt(self, code: str, error_message: str) -> str:
        """Build initial prompt with error context."""
        return f"""I need you to fix this Python code that has an error.

ERROR MESSAGE:
```
{error_message}
```

CURRENT CODE:
```python
{code}
```

Please investigate the error using the available tools and fix the code.
Start by searching for relevant definitions to understand the correct API."""
    
    def _build_tool_result_prompt(self, tool_results: List[Dict]) -> str:
        """Build prompt with tool execution results."""
        results_text = ""
        for tr in tool_results:
            results_text += f"\n### Tool: {tr['tool']}\n"
            results_text += f"Parameters: {json.dumps(tr['params'])}\n"
            results_text += f"Result:\n```\n{tr['result'][:2000]}\n```\n"
        
        return f"""Tool execution results:
{results_text}

Based on these results, continue investigating or submit your fix using submit_fix tool."""
    
    def _build_retry_prompt(self, code: str, test_output: str, explanation: str) -> str:
        """Build prompt for retry after failed fix."""
        return f"""Your fix attempt failed. Here's what happened:

YOUR FIX EXPLANATION:
{explanation}

TEST OUTPUT (still failing):
```
{test_output[:2000]}
```

CURRENT CODE (with your fix applied):
```python
{code[:3000]}
```

Please investigate further using tools and try again. 
Look for what you might have missed in the API or data structures."""
    
    def _build_guidance_prompt(self, code: str, error_message: str) -> str:
        """Build guidance prompt when AI doesn't use tools."""
        return f"""You haven't used any tools yet. To fix this error effectively, you should:

1. Use find_definition to find the function that's causing the error
2. Use read_file to understand the full API signature
3. Then use submit_fix with the corrected code

ERROR: {error_message[:500]}

Please start by using find_definition or search_code to investigate."""
    
    def _call_ai_with_tools(self, system_prompt: str, user_prompt: str) -> str:
        """Call AI with the given prompts."""
        try:
            from utils.models import LLMCallConfig
        except ImportError:
            from AutoGenChecker.utils.models import LLMCallConfig
        
        full_prompt = f"""{system_prompt}

---

{user_prompt}"""
        
        config = LLMCallConfig(
            temperature=0.2,
            max_tokens=8000,
        )
        
        try:
            response = self.llm_client.complete(full_prompt, config=config)
            return response.text
        except Exception as e:
            return f"Error calling AI: {e}"
    
    def _parse_tool_calls(self, response: str) -> Tuple[List[Dict], str]:
        """Parse tool calls from AI response."""
        tool_calls = []
        
        # Find all tool_call blocks
        pattern = r'```tool_call\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                if 'name' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        
        # Remove tool_call blocks from response to get final text
        final_response = re.sub(pattern, '', response, flags=re.DOTALL).strip()
        
        return tool_calls, final_response
    
    def _execute_tool(self, tool_call: Dict) -> str:
        """Execute a tool call and return result."""
        name = tool_call.get('name', '')
        params = tool_call.get('parameters', {})
        
        if name == 'search_code':
            return self._tool_search_code(
                params.get('pattern', ''),
                params.get('is_regex', False),
                params.get('file_pattern', '**/*.py')
            )
        
        elif name == 'read_file':
            return self._tool_read_file(
                params.get('file_path', ''),
                params.get('start_line'),
                params.get('end_line')
            )
        
        elif name == 'find_definition':
            return self._tool_find_definition(
                params.get('name', ''),
                params.get('type', 'any')
            )
        
        elif name == 'submit_fix':
            # This is handled specially in the main loop
            return "Fix submitted for testing"
        
        else:
            return f"Unknown tool: {name}"
    
    def _tool_search_code(
        self, 
        pattern: str, 
        is_regex: bool = False,
        file_pattern: str = '**/*.py'
    ) -> str:
        """Search for pattern in codebase."""
        results = []
        
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            
            for py_file in search_path.glob(file_pattern):
                if not py_file.is_file():
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        if is_regex:
                            if re.search(pattern, line):
                                results.append(f"{py_file}:{i}: {line.strip()}")
                        else:
                            if pattern.lower() in line.lower():
                                results.append(f"{py_file}:{i}: {line.strip()}")
                        
                        if len(results) >= 20:
                            break
                except Exception:
                    continue
                
                if len(results) >= 20:
                    break
            
            if len(results) >= 20:
                break
        
        if not results:
            return f"No matches found for pattern: {pattern}"
        
        return "\n".join(results[:20])
    
    def _tool_read_file(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None
    ) -> str:
        """Read file contents."""
        # Try to resolve the path
        path = Path(file_path)
        
        if not path.is_absolute():
            # Try different base paths
            for search_path in self.search_paths:
                candidate = search_path / file_path
                if candidate.exists():
                    path = candidate
                    break
            else:
                # Try glob search
                for search_path in self.search_paths:
                    matches = list(search_path.glob(f"**/{file_path}"))
                    if matches:
                        path = matches[0]
                        break
        
        if not path.exists():
            return f"File not found: {file_path}"
        
        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            if start_line is not None or end_line is not None:
                start = (start_line or 1) - 1
                end = end_line or len(lines)
                lines = lines[start:end]
                content = '\n'.join(lines)
            
            # Truncate if too long
            if len(content) > 5000:
                content = content[:5000] + "\n... (truncated)"
            
            return f"File: {path}\n\n{content}"
        
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _tool_find_definition(self, name: str, def_type: str = 'any') -> str:
        """Find function/class/method definition."""
        results = []
        
        # Build search patterns based on type
        patterns = []
        if def_type in ('any', 'function'):
            patterns.append(rf'^\s*def\s+{re.escape(name)}\s*\(')
        if def_type in ('any', 'class'):
            patterns.append(rf'^\s*class\s+{re.escape(name)}\s*[\(:]')
        if def_type in ('any', 'method'):
            patterns.append(rf'^\s+def\s+{re.escape(name)}\s*\(')
        
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
            
            for py_file in search_path.glob('**/*.py'):
                if not py_file.is_file():
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if re.search(pattern, line):
                                # Get context (signature + docstring + some body)
                                context_end = min(i + 50, len(lines))
                                context = '\n'.join(lines[i-1:context_end])
                                
                                # Try to extract just the signature
                                sig_match = re.search(
                                    rf'(def\s+{re.escape(name)}\s*\([^)]*\)[^:]*:)',
                                    context,
                                    re.DOTALL
                                )
                                if sig_match:
                                    signature = sig_match.group(1)
                                else:
                                    signature = line.strip()
                                
                                results.append({
                                    'file': str(py_file),
                                    'line': i,
                                    'signature': signature,
                                    'context': context[:1500]
                                })
                                break
                
                except Exception:
                    continue
        
        if not results:
            return f"Definition not found for: {name}"
        
        output = []
        for r in results[:3]:  # Limit to 3 results
            output.append(f"Found in {r['file']} at line {r['line']}:")
            output.append(f"Signature: {r['signature']}")
            output.append(f"Context:\n```python\n{r['context']}\n```\n")
        
        return '\n'.join(output)
    
    def _run_test(
        self,
        code: str,
        test_command: str,
        checker_path: Optional[Path] = None
    ) -> Tuple[bool, str]:
        """Run test to verify fix."""
        if checker_path:
            # Write the fixed code to the file
            try:
                checker_path.write_text(code, encoding='utf-8')
            except Exception as e:
                return False, f"Failed to write code: {e}"
        
        # Run the test
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.work_dir)
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            return success, output
        
        except subprocess.TimeoutExpired:
            return False, "Test timed out (60s)"
        except Exception as e:
            return False, f"Test execution error: {e}"


def create_agentic_fixer(
    work_dir: Path,
    llm_provider: str = "jedai",
    llm_model: str = "claude-sonnet-4-5",
    max_iterations: int = 5,
    verbose: bool = True
) -> AgenticFixer:
    """
    Factory function to create an AgenticFixer with proper LLM client.
    
    Args:
        work_dir: Working directory
        llm_provider: LLM provider (jedai, openai, etc.)
        llm_model: Model name
        max_iterations: Max fix attempts
        verbose: Print progress
        
    Returns:
        Configured AgenticFixer instance
    """
    try:
        from llm_clients import create_llm_client
    except ImportError:
        from AutoGenChecker.llm_clients import create_llm_client
    
    llm_client = create_llm_client(llm_provider, model=llm_model)
    
    return AgenticFixer(
        work_dir=work_dir,
        llm_client=llm_client,
        max_iterations=max_iterations,
        verbose=verbose
    )
