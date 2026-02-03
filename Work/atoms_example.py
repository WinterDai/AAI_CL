"""
Atom A/B/C示例实现 - 符合Plan_v2.txt规范

这是一个参考实现，展示如何实现符合Plan_v2.txt所有规范的Atom函数。
实际项目中，这些函数应由LLM根据agent_guide.txt生成，并根据具体需求定制。
"""

import re
import fnmatch
from typing import List, Dict, Any, Optional


# ============================================================================
# ATOM A: extract_context
# ============================================================================

def extract_context(text: str, source_file: str) -> List[Dict[str, Any]]:
    """
    Atom A: Context Extractor (Plan_v2.txt Section 1 - Locked)
    
    [Locked] 函数名称: extract_context
    [Locked] 参数:
        - text: str - 文件内容（由L1 IO Engine提供）
        - source_file: str - 源文件绝对路径（用于元数据追踪）
    [Locked] 返回: List[ParsedItem]
    
    约束:
    1. NO IO allowed - Atom A不得进行任何文件读取
    2. PR5: 不得根据requirements/waivers过滤结果
    3. Value Type Hard Lock: 所有'value'字段必须转换为str类型
    
    这是一个示例实现，解析日志文件中的ERROR和WARNING消息。
    实际应用中应根据具体文件格式定制。
    """
    results = []
    
    # 示例：解析ERROR和WARNING消息
    lines = text.split('\n')
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # 简单示例：匹配包含ERROR或WARNING的行
        if 'ERROR' in stripped or 'WARNING' in stripped:
            # 提取消息
            results.append({
                "value": stripped,  # 将在Standardization Layer转为str
                "line_number": line_num,
                "matched_content": stripped,
                "parsed_fields": {}  # 可以包含更多提取的字段
            })
    
    # [Locked] Standardization Layer (Plan_v2.txt Section 1 - MANDATORY)
    # 强制执行数据接口契约，防止 Layer 3 崩溃
    standardized_output = []
    for item in results:
        # [Critical] Ensure value is string (Gate 1 Requirement)
        safe_value = str(item.get("value", ""))
        
        standardized_item = {
            "value": safe_value,                      # 强制转换为str
            "source_file": source_file,               # 透传元数据
            "line_number": item.get("line_number"),   # 允许None
            "matched_content": str(item.get("matched_content", "")),
            "parsed_fields": item.get("parsed_fields", {})  # 必须是非None字典
        }
        standardized_output.append(standardized_item)
        
    return standardized_output


# ============================================================================
# ATOM B: validate_logic
# ============================================================================

def validate_logic(
    text: str, 
    pattern: str, 
    parsed_fields: Optional[Dict] = None,
    default_match: str = "contains",  # Layer 3/4 注入点
    regex_mode: str = "search"        # Layer 3/4 注入点
) -> Dict[str, Any]:
    """
    Atom B: Universal Logic Validator (Plan_v2.txt Section 1 - Locked)
    
    Logic: Alternatives > Regex > Wildcard > Default
    Supports: Check Logic (contains/search) AND Waiver Logic (exact/match)
    
    [Locked] MatchResult Schema:
    {
        'is_match': bool,
        'reason': str,
        'kind': str  # "exact", "contains", "wildcard", "regex", "alternatives"
    }
    """
    # [Locked] None Safety (Gate 2 Test #1)
    if parsed_fields is None:
        parsed_fields = {}

    # 1. Alternatives Logic ('|') - Highest Precedence
    # Note: Regex/Wildcard chars inside alternatives are treated as LITERALS
    if '|' in pattern:
        segments = [s.strip() for s in pattern.split('|') if s.strip()]
        for seg in segments:
            # Alternatives always use 'contains' semantics
            if seg in text:
                return {'is_match': True, 'reason': f"Alternative '{seg}' found", 'kind': 'alternatives'}
        return {'is_match': False, 'reason': "No alternatives found", 'kind': 'alternatives'}

    # 2. Regex Logic (startswith 'regex:')
    # [Locked] Must have "regex:" prefix (Plan_v2.txt Section 1)
    if pattern.startswith("regex:"):
        raw_regex = pattern[6:]  # Strip "regex:" prefix
        try:
            # Policy Injection: Check uses 'search', Waiver uses 'match'
            mode = regex_mode if regex_mode in {"search", "match"} else "search"
            
            if mode == 'match':
                match = re.match(raw_regex, text)
            else:
                match = re.search(raw_regex, text)
                
            if match:
                return {'is_match': True, 'reason': "Regex matched", 'kind': 'regex'}
            else:
                return {'is_match': False, 'reason': "Regex not matched", 'kind': 'regex'}
        except re.error as e:
            # [Locked] Must handle bad regex gracefully (Gate 2 Test #3)
            return {'is_match': False, 'reason': f"Invalid Regex: {str(e)}", 'kind': 'regex'}

    # 3. Wildcard Logic ('*' or '?')
    # [Locked] Must use fnmatchcase for case sensitivity
    if '*' in pattern or '?' in pattern:
        if fnmatch.fnmatchcase(text, pattern):
            return {'is_match': True, 'reason': "Wildcard matched", 'kind': 'wildcard'}
        else:
            return {'is_match': False, 'reason': "Wildcard not matched", 'kind': 'wildcard'}

    # 4. Default Logic (String Literal)
    # Policy Injection: Check uses 'contains', Waiver uses 'exact'
    mode = default_match if default_match in {"contains", "exact"} else "contains"
    
    if mode == "exact":
        is_hit = (text == pattern)
    else:
        is_hit = (pattern in text)

    return {
        'is_match': is_hit, 
        'reason': f"Default {mode} check", 
        'kind': mode
    }


# ============================================================================
# ATOM C: check_existence
# ============================================================================

def check_existence(items: List[Dict]) -> Dict:
    """
    Atom C: Existence Checker (Plan_v2.txt Section 1 - Locked)
    
    Used ONLY by Type 1 / Type 4 runners.
    Required for Gate 1 Signature Compliance.
    
    输入:
        items: List[ParsedItem] - Atom A返回的所有items
        
    输出:
        {
            'is_match': bool,
            'reason': str,
            'evidence': List[ParsedItem]  # [Locked] Must pass evidence back to Framework
        }
    """
    # Logic: If items extracted > 0, existence is proved.
    if items and len(items) > 0:
        return {
            'is_match': True, 
            'reason': f"Found {len(items)} items", 
            'evidence': items  # [Locked] Must pass evidence back to Framework
        }
    else:
        return {
            'is_match': False, 
            'reason': "No items found", 
            'evidence': []
        }


# ============================================================================
# Gate 1 & Gate 2 测试验证
# ============================================================================

def run_gate1_tests():
    """Gate 1: Atomic Integrity (Signature + Schema + Value Type)"""
    print("\n" + "="*60)
    print("Gate 1: Atomic Integrity Tests")
    print("="*60)
    
    # Test 1: Signature Check
    text = "ERROR: test message\nWARNING: another message"
    source_file = "/test/file.log"
    items = extract_context(text, source_file)
    
    print(f"✓ Atom A signature correct: extract_context(text, source_file)")
    print(f"✓ Returned {len(items)} items")
    
    # Test 2: Schema Check
    required_keys = {'value', 'source_file', 'line_number', 'matched_content', 'parsed_fields'}
    for item in items:
        assert set(item.keys()) == required_keys, f"Schema mismatch: {set(item.keys())}"
    print(f"✓ Schema correct: all items have required keys")
    
    # Test 3: Value Type Safety
    for item in items:
        assert isinstance(item['value'], str), f"ParsedItem['value'] must be str, got {type(item['value'])}"
    print(f"✓ Value type safety: all values are str")
    
    print("\n✅ Gate 1 ALL TESTS PASSED\n")


def run_gate2_tests():
    """Gate 2: Matcher Robustness & Precedence (Atom B)"""
    print("\n" + "="*60)
    print("Gate 2: Matcher Robustness Tests")
    print("="*60)
    
    # Test 1: None-Safety
    result = validate_logic("abc", "a", parsed_fields=None)
    assert result is not None, "Test 1 failed"
    print("✓ Test 1: None-Safety passed")
    
    # Test 2: Empty Alternatives
    result = validate_logic("abc", "|a||")
    assert result['is_match'] == True and result['kind'] == "alternatives", "Test 2 failed"
    print("✓ Test 2: Empty Alternatives passed")
    
    # Test 3: Bad Regex
    result = validate_logic("abc", "regex:[", regex_mode="search")
    assert result['is_match'] == False and result['kind'] == "regex", "Test 3 failed"
    assert "Invalid Regex:" in result['reason'], "Test 3 failed"
    print("✓ Test 3: Bad Regex handled gracefully")
    
    # Test 4: Literal Alternatives
    result1 = validate_logic("regex:^a", "regex:^a|zzz")
    result2 = validate_logic("abc", "regex:^a|zzz")
    assert result1['is_match'] == True, "Test 4.1 failed"
    assert result2['is_match'] == False, "Test 4.2 failed"
    print("✓ Test 4: Literal Alternatives (regex chars as literals)")
    
    # Test 5: Wildcard Priority
    result = validate_logic("abc", "a*c")
    assert result['kind'] == "wildcard", "Test 5 failed"
    print("✓ Test 5: Wildcard Priority correct")
    
    # Test 6: Default Strategy Policy
    result1 = validate_logic("abc", "b", default_match="contains")
    result2 = validate_logic("abc", "b", default_match="exact")
    assert result1['is_match'] == True and result1['kind'] == "contains", "Test 6.1 failed"
    assert result2['is_match'] == False and result2['kind'] == "exact", "Test 6.2 failed"
    print("✓ Test 6: Default Strategy Policy works")
    
    # Test 7: regex_mode Invalid Value
    result = validate_logic("abc", "regex:^a", regex_mode="BAD")
    assert result is not None, "Test 7 failed: should not raise exception"
    print("✓ Test 7: Invalid regex_mode handled gracefully")
    
    print("\n✅ Gate 2 ALL TESTS PASSED\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ATOMS EXAMPLE - Plan_v2.txt Compliance Test")
    print("="*60)
    
    # Run Gate tests
    run_gate1_tests()
    run_gate2_tests()
    
    # Demo usage
    print("\n" + "="*60)
    print("Usage Demo")
    print("="*60)
    
    # Demo Atom A
    text = "Line 1: Normal log\nLine 2: ERROR - Something failed\nLine 3: WARNING - Check this"
    items = extract_context(text, "/demo/file.log")
    print(f"\nAtom A extracted {len(items)} items:")
    for item in items:
        print(f"  - Line {item['line_number']}: {item['value']}")
    
    # Demo Atom B
    test_cases = [
        ("ERROR - Something failed", "ERROR", "contains"),
        ("test.log", "*.log", None),
        ("ERROR 123", "regex:ERROR [0-9]+", None),
        ("A|B|C", "B|Z|Y", None)
    ]
    
    print(f"\nAtom B matching tests:")
    for text, pattern, mode in test_cases:
        kwargs = {'default_match': mode} if mode else {}
        result = validate_logic(text, pattern, **kwargs)
        print(f"  '{text}' vs '{pattern}': {result['is_match']} ({result['kind']})")
    
    # Demo Atom C
    print(f"\nAtom C existence check:")
    result = check_existence(items)
    print(f"  {len(items)} items → {result['is_match']}: {result['reason']}")
    
    print("\n" + "="*60)
    print("✅ ALL DEMOS COMPLETED")
    print("="*60 + "\n")
