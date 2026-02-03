"""
Developer Agent - I/O Formatter
Converts Agent inputs/outputs to readable Markdown format for debugging and review.

Provides:
1. Console output formatting with colors and structure
2. Markdown file generation for detailed review
3. Summary views for quick overview
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'


def _truncate(text: str, max_len: int = 500, suffix: str = "...") -> str:
    """Truncate text with suffix if exceeds max length"""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def _extract_sections(prompt: str) -> Dict[str, str]:
    """Extract sections from a prompt based on markdown headers"""
    sections = {}
    current_section = "preamble"
    current_content = []
    
    for line in prompt.split('\n'):
        # Check for markdown headers
        if line.startswith('# ') and not line.startswith('# ==='):
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[2:].strip()
            current_content = []
        elif line.startswith('## '):
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif line.startswith('---'):
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = "separator"
            current_content = []
        else:
            current_content.append(line)
    
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections


def _extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from response"""
    blocks = []
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for lang, code in matches:
        blocks.append({
            'language': lang or 'text',
            'code': code.strip()
        })
    
    return blocks


def format_prompt_to_markdown(stage: str, prompt: str, include_full: bool = False) -> str:
    """
    Convert a prompt to readable Markdown format
    
    Args:
        stage: Stage name (agent_a, agent_b, reflect_a, etc.)
        prompt: The raw prompt text
        include_full: Whether to include full content or summarized
        
    Returns:
        Formatted Markdown string
    """
    sections = _extract_sections(prompt)
    
    stage_titles = {
        'agent_a': '🔍 Agent A (Parsing Expert)',
        'agent_b': '⚙️ Agent B (Logic Developer)',
        'reflect_a': '🔄 Reflect A (Fix Atom A)',
        'reflect_b': '🔄 Reflect B (Fix Atom B/C)',
    }
    
    title = stage_titles.get(stage, f'📋 {stage.upper()}')
    
    lines = [
        f"# {title} - Prompt Input",
        f"",
        f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Length:** {len(prompt):,} characters",
        f"",
        "---",
        ""
    ]
    
    # Add summary of sections
    lines.append("## 📑 Sections Overview")
    lines.append("")
    lines.append("| Section | Size |")
    lines.append("|---------|------|")
    for section, content in sections.items():
        if section != "separator":
            lines.append(f"| {section[:40]} | {len(content):,} chars |")
    lines.append("")
    
    # Add key sections with truncation
    key_sections = ['Role', 'The 10.2 Hard Constraints (NON-NEGOTIABLE)', 
                    'Gate 2 Test Vectors (YOUR CODE MUST PASS ALL)',
                    'CRITICAL: Zero Hardcoding Policy', 'Task']
    
    lines.append("## 🎯 Key Constraints")
    lines.append("")
    
    for key in key_sections:
        if key in sections:
            content = sections[key]
            if include_full:
                lines.append(f"### {key}")
                lines.append("")
                lines.append(content)
            else:
                lines.append(f"### {key}")
                lines.append("")
                lines.append(_truncate(content, 500))
            lines.append("")
    
    # Add ItemSpec summary if present
    if 'ItemSpec Content' in sections:
        lines.append("## 📄 ItemSpec Content")
        lines.append("")
        content = sections['ItemSpec Content']
        if include_full:
            lines.append(content)
        else:
            # Extract just the key info
            lines.append(f"**Size:** {len(content):,} characters")
            lines.append("")
            lines.append("**Preview:**")
            lines.append("```")
            lines.append(_truncate(content, 800))
            lines.append("```")
        lines.append("")
    
    # Add log snippets summary if present
    if 'Real Log Snippets' in sections:
        content = sections['Real Log Snippets']
        lines.append("## 📋 Log Snippets")
        lines.append("")
        if content.strip() == '{}' or content.strip() == '':
            lines.append("*No log snippets provided*")
        else:
            lines.append(f"**Size:** {len(content):,} characters")
            if include_full:
                lines.append("")
                lines.append("```json")
                lines.append(content)
                lines.append("```")
        lines.append("")
    
    return '\n'.join(lines)


def format_response_to_markdown(stage: str, response: str, include_full: bool = False) -> str:
    """
    Convert an LLM response to readable Markdown format
    
    Args:
        stage: Stage name
        response: The raw response text
        include_full: Whether to include full code or summarized
        
    Returns:
        Formatted Markdown string
    """
    stage_titles = {
        'agent_a': '🔍 Agent A (Parsing Expert)',
        'agent_b': '⚙️ Agent B (Logic Developer)',
        'reflect_a': '🔄 Reflect A (Fix Atom A)',
        'reflect_b': '🔄 Reflect B (Fix Atom B/C)',
    }
    
    title = stage_titles.get(stage, f'📋 {stage.upper()}')
    
    lines = [
        f"# {title} - LLM Response",
        f"",
        f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Length:** {len(response):,} characters",
        f"",
        "---",
        ""
    ]
    
    # Extract code blocks
    code_blocks = _extract_code_blocks(response)
    
    lines.append("## 📊 Response Summary")
    lines.append("")
    lines.append(f"- **Code Blocks Found:** {len(code_blocks)}")
    
    for i, block in enumerate(code_blocks):
        lang = block['language']
        code_len = len(block['code'])
        lines.append(f"  - Block {i+1}: `{lang}` ({code_len:,} chars)")
    lines.append("")
    
    # Add code blocks
    for i, block in enumerate(code_blocks):
        lang = block['language']
        code = block['code']
        
        if lang == 'python':
            # Extract function names
            func_pattern = r'def (\w+)\s*\('
            funcs = re.findall(func_pattern, code)
            
            lines.append(f"## 🐍 Python Code Block {i+1}")
            lines.append("")
            if funcs:
                lines.append(f"**Functions Defined:** `{'`, `'.join(funcs)}`")
                lines.append("")
            
            if include_full:
                lines.append("```python")
                lines.append(code)
                lines.append("```")
            else:
                lines.append("**Preview:**")
                lines.append("```python")
                lines.append(_truncate(code, 1500))
                lines.append("```")
            lines.append("")
            
        elif lang == 'yaml':
            lines.append(f"## 📝 YAML Configuration")
            lines.append("")
            if include_full:
                lines.append("```yaml")
                lines.append(code)
                lines.append("```")
            else:
                lines.append("**Preview:**")
                lines.append("```yaml")
                lines.append(_truncate(code, 800))
                lines.append("```")
            lines.append("")
        else:
            lines.append(f"## 📄 {lang.upper() if lang else 'Text'} Block {i+1}")
            lines.append("")
            lines.append(f"```{lang}")
            lines.append(_truncate(code, 500) if not include_full else code)
            lines.append("```")
            lines.append("")
    
    # Add reasoning if present (text outside code blocks)
    reasoning = re.sub(r'```\w*\n.*?```', '', response, flags=re.DOTALL).strip()
    if reasoning:
        lines.append("## 💭 Reasoning")
        lines.append("")
        if include_full:
            lines.append(reasoning)
        else:
            lines.append(_truncate(reasoning, 500))
        lines.append("")
    
    return '\n'.join(lines)


def format_validation_to_markdown(gate_results: Dict[str, bool], errors: List[str]) -> str:
    """
    Convert validation results to readable Markdown format
    
    Args:
        gate_results: Dictionary of gate test results
        errors: List of error messages
        
    Returns:
        Formatted Markdown string
    """
    lines = [
        "# 🔬 Validation Results",
        "",
        f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        ""
    ]
    
    # Summary
    total = len(gate_results)
    passed = sum(1 for v in gate_results.values() if v)
    failed = total - passed
    
    status_emoji = "✅" if failed == 0 else "❌"
    lines.append(f"## {status_emoji} Summary: {passed}/{total} Gates Passed")
    lines.append("")
    
    # Gate results table
    lines.append("## 📋 Gate Results")
    lines.append("")
    lines.append("| Gate | Status | Description |")
    lines.append("|------|--------|-------------|")
    
    gate_descriptions = {
        'gate1_signature': 'Required function signatures present',
        'gate1_schema': 'Output schema compliance',
        'gate1_type_safety': 'Value field is string type',
        'gate1_evidence': 'Evidence passthrough works',
        'gate2_none_safety': 'Handles parsed_fields=None',
        'gate2_alternatives': 'Empty alternatives `|a||` works',
        'gate2_bad_regex': 'Catches invalid regex gracefully',
        'gate2_literal_alt': 'Literal alternatives before regex',
        'gate2_precedence': 'Wildcard uses fnmatch',
        'gate2_default_strategy': 'Contains vs exact matching',
        'gate2_invalid_mode': 'Invalid regex_mode defaults to search',
        'consistency': 'YAML and code are consistent',
    }
    
    for gate, passed in gate_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        desc = gate_descriptions.get(gate, gate)
        lines.append(f"| `{gate}` | {status} | {desc} |")
    
    lines.append("")
    
    # Errors if any
    if errors:
        lines.append("## ⚠️ Errors")
        lines.append("")
        for i, error in enumerate(errors, 1):
            lines.append(f"{i}. {error}")
        lines.append("")
    
    return '\n'.join(lines)


def print_formatted_prompt(stage: str, prompt: str):
    """Print formatted prompt to console with colors"""
    stage_colors = {
        'agent_a': Colors.CYAN,
        'agent_b': Colors.GREEN,
        'reflect_a': Colors.YELLOW,
        'reflect_b': Colors.YELLOW,
    }
    
    color = stage_colors.get(stage, Colors.BLUE)
    
    print(f"\n{Colors.BOLD}{color}{'═' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{color}📥 [{stage.upper()}] PROMPT INPUT{Colors.END}")
    print(f"{Colors.BOLD}{color}{'═' * 80}{Colors.END}")
    
    # Print summary
    sections = _extract_sections(prompt)
    print(f"\n{Colors.DIM}Total: {len(prompt):,} chars | Sections: {len(sections)}{Colors.END}")
    
    # Print key sections briefly
    print(f"\n{Colors.BOLD}📑 Sections:{Colors.END}")
    for section in list(sections.keys())[:8]:
        if section != "separator":
            size = len(sections[section])
            print(f"  • {section[:50]}: {size:,} chars")
    
    if len(sections) > 8:
        print(f"  ... and {len(sections) - 8} more sections")
    
    print(f"\n{Colors.DIM}{'─' * 80}{Colors.END}\n")


def print_formatted_response(stage: str, response: str):
    """Print formatted response to console with colors"""
    stage_colors = {
        'agent_a': Colors.CYAN,
        'agent_b': Colors.GREEN,
        'reflect_a': Colors.YELLOW,
        'reflect_b': Colors.YELLOW,
    }
    
    color = stage_colors.get(stage, Colors.BLUE)
    
    print(f"\n{Colors.BOLD}{color}{'═' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{color}📤 [{stage.upper()}] LLM RESPONSE{Colors.END}")
    print(f"{Colors.BOLD}{color}{'═' * 80}{Colors.END}")
    
    # Extract and summarize code blocks
    code_blocks = _extract_code_blocks(response)
    
    print(f"\n{Colors.DIM}Total: {len(response):,} chars | Code Blocks: {len(code_blocks)}{Colors.END}")
    
    for i, block in enumerate(code_blocks):
        lang = block['language']
        code = block['code']
        
        if lang == 'python':
            # Extract function names
            func_pattern = r'def (\w+)\s*\('
            funcs = re.findall(func_pattern, code)
            
            print(f"\n{Colors.BOLD}🐍 Python Block {i+1}:{Colors.END}")
            if funcs:
                print(f"  Functions: {Colors.GREEN}{', '.join(funcs)}{Colors.END}")
            print(f"  Size: {len(code):,} chars")
            
            # Show first few lines
            preview_lines = code.split('\n')[:5]
            print(f"\n{Colors.DIM}  Preview:{Colors.END}")
            for line in preview_lines:
                print(f"  {Colors.DIM}{line[:70]}{Colors.END}")
            if len(code.split('\n')) > 5:
                print(f"  {Colors.DIM}... ({len(code.split(chr(10))) - 5} more lines){Colors.END}")
                
        elif lang == 'yaml':
            print(f"\n{Colors.BOLD}📝 YAML Config:{Colors.END}")
            print(f"  Size: {len(code):,} chars")
            
            # Show first few lines
            preview_lines = code.split('\n')[:5]
            print(f"\n{Colors.DIM}  Preview:{Colors.END}")
            for line in preview_lines:
                print(f"  {Colors.DIM}{line[:70]}{Colors.END}")
    
    print(f"\n{Colors.DIM}{'─' * 80}{Colors.END}\n")


def print_formatted_validation(gate_results: Dict[str, bool], errors: List[str]):
    """Print formatted validation results to console with colors"""
    total = len(gate_results)
    passed = sum(1 for v in gate_results.values() if v)
    failed = total - passed
    
    if failed == 0:
        status_color = Colors.GREEN
        status_emoji = "✅"
    else:
        status_color = Colors.RED
        status_emoji = "❌"
    
    print(f"\n{Colors.BOLD}{status_color}{'═' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{status_color}🔬 VALIDATION RESULTS: {status_emoji} {passed}/{total} Gates Passed{Colors.END}")
    print(f"{Colors.BOLD}{status_color}{'═' * 80}{Colors.END}")
    
    # Gate results
    print(f"\n{Colors.BOLD}📋 Gate Results:{Colors.END}")
    
    for gate, result in gate_results.items():
        if result:
            print(f"  {Colors.GREEN}✅ {gate}{Colors.END}")
        else:
            print(f"  {Colors.RED}❌ {gate}{Colors.END}")
    
    # Errors
    if errors:
        print(f"\n{Colors.BOLD}{Colors.RED}⚠️ Errors:{Colors.END}")
        for error in errors:
            print(f"  {Colors.RED}• {error[:100]}{Colors.END}")
    
    print(f"\n{Colors.DIM}{'─' * 80}{Colors.END}\n")


def save_io_as_markdown(
    output_dir: str,
    item_id: str,
    stage: str,
    prompt: str = None,
    response: str = None,
    gate_results: Dict[str, bool] = None,
    errors: List[str] = None,
    iteration: int = 0
):
    """
    Save I/O as Markdown files for detailed review
    
    Directory Structure:
        {output_dir}/
            markdown/
                iteration_0/
                    01_agent_a_prompt.md
                    02_agent_a_response.md
                    03_agent_b_prompt.md
                    04_agent_b_response.md
                    05_validation.md
                iteration_1/  (if reflect triggered)
                    06_reflect_a_prompt.md
                    07_reflect_a_response.md
                    08_validation.md
    
    Args:
        output_dir: Directory to save markdown files (item-level, e.g. Test/Codegen/IMP-10-0-0-00)
        item_id: Item identifier (used for labeling, NOT for path creation)
        stage: Stage name (agent_a, agent_b, reflect_a, reflect_b, validation)
        prompt: Prompt text (optional)
        response: Response text (optional)
        gate_results: Validation results (optional)
        errors: Error list (optional)
        iteration: Current iteration round (0-based, used for subdirectory)
    """
    # Create markdown output directory (directly under output_dir)
    md_dir = os.path.join(output_dir, "markdown", f"iteration_{iteration}")
    os.makedirs(md_dir, exist_ok=True)
    
    # Determine sequence number based on stage and iteration
    stage_sequence = {
        'agent_a': 1,
        'agent_b': 3,
        'validation': 5,
        'reflect_a': 6,
        'reflect_b': 7,
    }
    
    base_seq = stage_sequence.get(stage, 0)
    
    timestamp = datetime.now().strftime('%H%M%S')
    
    if prompt:
        seq = base_seq
        prompt_md = format_prompt_to_markdown(stage, prompt, include_full=True)
        # Add iteration info to header
        prompt_md = prompt_md.replace(
            f"**Timestamp:**", 
            f"**Item:** {item_id}  \n**Iteration:** {iteration}  \n**Timestamp:**"
        )
        prompt_file = os.path.join(md_dir, f"{seq:02d}_{stage}_prompt.md")
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_md)
        print(f"  [FILE] Saved: {prompt_file}")
    
    if response:
        seq = base_seq + 1
        response_md = format_response_to_markdown(stage, response, include_full=True)
        # Add iteration info to header
        response_md = response_md.replace(
            f"**Timestamp:**",
            f"**Item:** {item_id}  \n**Iteration:** {iteration}  \n**Timestamp:**"
        )
        response_file = os.path.join(md_dir, f"{seq:02d}_{stage}_response.md")
        with open(response_file, 'w', encoding='utf-8') as f:
            f.write(response_md)
        print(f"  [FILE] Saved: {response_file}")
    
    if gate_results is not None:
        seq = stage_sequence.get('validation', 5)
        validation_md = format_validation_to_markdown(gate_results, errors or [])
        # Add iteration info to header
        validation_md = validation_md.replace(
            f"**Timestamp:**",
            f"**Item:** {item_id}  \n**Iteration:** {iteration}  \n**Timestamp:**"
        )
        validation_file = os.path.join(md_dir, f"{seq:02d}_validation.md")
        with open(validation_file, 'w', encoding='utf-8') as f:
            f.write(validation_md)
        print(f"  [FILE] Saved: {validation_file}")
