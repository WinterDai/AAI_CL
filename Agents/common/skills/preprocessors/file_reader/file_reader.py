"""
File Reader Preprocessor

Preprocessor: 无条件执行，纯数据提取
职责: 读取文件样本，检测格式，供 LLM 进行语义分析

版本: 1.0.0
"""

import re
from pathlib import Path
from typing import Optional, List
from collections import Counter
from dataclasses import dataclass, field


# ============================================================================
# 本地数据类 (与 models.py 保持兼容)
# ============================================================================

@dataclass
class PatternMatch:
    """模式匹配结果"""
    pattern: str
    count: int
    sample: str
    
    def to_dict(self) -> dict:
        return {"pattern": self.pattern, "count": self.count, "sample": self.sample}


@dataclass
class FileAnalysis:
    """文件分析结果"""
    files_analyzed: int
    total_lines_sampled: int
    detected_format: str  # log/report/csv/json/custom
    common_patterns: List[PatternMatch] = field(default_factory=list)
    section_headers: List[str] = field(default_factory=list)
    sample_lines: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "files_analyzed": self.files_analyzed,
            "total_lines_sampled": self.total_lines_sampled,
            "detected_format": self.detected_format,
            "common_patterns": [p.to_dict() for p in self.common_patterns],
            "section_headers": self.section_headers,
            "sample_lines": self.sample_lines
        }


# ============================================================================
# 常见模式库
# ============================================================================

# 常见模式库 (用于辅助检测，不作为主要分析依据)
COMMON_PATTERNS = [
    (r'\*\*ERROR:\s*\(([A-Z]+-\d+)\)', 'error_code'),
    (r'\*\*WARN:\s*\(([A-Z]+-\d+)\)', 'warning_code'),
    (r'\*\*INFO:\s*(.+)', 'info_message'),
    (r'Slack:\s*([-\d.]+)', 'slack_value'),
    (r'Path Group:\s*(\S+)', 'path_group'),
    (r'Endpoint:\s*(\S+)', 'endpoint'),
    (r'^={20,}', 'section_separator'),
    (r'^-{20,}', 'line_separator'),
    (r'^\s*(\w+):\s*(.+)$', 'key_value'),
]


# ============================================================================
# 编码检测
# ============================================================================

def _detect_encoding(file_path: Path) -> str:
    """
    检测文件编码
    
    通过 BOM (Byte Order Mark) 检测常见编码:
    - UTF-16 LE: FF FE
    - UTF-16 BE: FE FF
    - UTF-8 BOM: EF BB BF
    - 无 BOM: 默认 UTF-8
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 编码名称
    """
    try:
        with open(file_path, 'rb') as f:
            # 读取前 4 字节检测 BOM
            bom = f.read(4)
            
            # UTF-16 LE (最常见于 Windows)
            if bom.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            
            # UTF-16 BE
            if bom.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            
            # UTF-8 with BOM
            if bom.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            
            # UTF-32 LE
            if bom.startswith(b'\xff\xfe\x00\x00'):
                return 'utf-32-le'
            
            # UTF-32 BE
            if bom.startswith(b'\x00\x00\xfe\xff'):
                return 'utf-32-be'
            
            # 无 BOM - 检测是否有大量 \x00 字节 (UTF-16 特征)
            f.seek(0)
            sample = f.read(1024)
            
            # 如果有很多 \x00 且间隔出现，可能是 UTF-16 无 BOM
            null_count = sample.count(b'\x00')
            if null_count > len(sample) * 0.3:
                # 检测是 LE 还是 BE
                if len(sample) >= 2 and sample[1] == 0:
                    return 'utf-16-le'
                elif len(sample) >= 2 and sample[0] == 0:
                    return 'utf-16-be'
            
            # 默认 UTF-8
            return 'utf-8'
            
    except Exception:
        return 'utf-8'


def read_files(
    file_paths: list[str], 
    lines_per_file: int = 100
) -> FileAnalysis:
    """
    读取文件样本，提取供 LLM 分析的数据
    
    Preprocessor 职责 (纯数据提取):
    ✓ 读取前 N 行内容
    ✓ 检测格式 (log/report/csv/json)
    ✓ 提取样本行
    
    不做 (留给 LLM):
    ✗ 理解数据含义
    ✗ 设计解析逻辑
    ✗ 选择正则表达式
    
    Args:
        file_paths: 输入文件路径列表
        lines_per_file: 每个文件读取的行数
        
    Returns:
        FileAnalysis: 文件分析结果 (供 LLM 进行语义理解)
    """
    all_lines = []
    files_analyzed = 0
    
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            continue
            
        try:
            # 自动检测编码
            encoding = _detect_encoding(path)
            with open(path, 'r', encoding=encoding, errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= lines_per_file:
                        break
                    lines.append(line.rstrip('\n\r'))
                all_lines.extend(lines)
                files_analyzed += 1
        except Exception:
            continue
    
    if not all_lines:
        return FileAnalysis(
            files_analyzed=0,
            total_lines_sampled=0,
            detected_format='unknown',
            common_patterns=[],
            section_headers=[],
            sample_lines=[]
        )
    
    # 检测格式
    detected_format = _detect_format(all_lines)
    
    # 提取常见模式 (辅助信息)
    common_patterns = _extract_patterns(all_lines)
    
    # 识别段落标题
    section_headers = _extract_section_headers(all_lines)
    
    # 选取代表性样本行 (更多样本供 LLM 分析)
    sample_lines = _select_sample_lines(all_lines, max_samples=20)
    
    return FileAnalysis(
        files_analyzed=files_analyzed,
        total_lines_sampled=len(all_lines),
        detected_format=detected_format,
        common_patterns=common_patterns,
        section_headers=section_headers,
        sample_lines=sample_lines
    )


def _detect_format(lines: list[str]) -> str:
    """
    检测文件格式
    
    基于确定性规则，不做语义理解
    """
    if not lines:
        return 'unknown'
    
    # 合并前几行检测
    sample = '\n'.join(lines[:20])
    
    # JSON 检测
    if sample.strip().startswith('{') or sample.strip().startswith('['):
        return 'json'
    
    # CSV 检测 (逗号分隔，多行)
    comma_lines = sum(1 for line in lines[:10] if ',' in line and line.count(',') >= 2)
    if comma_lines >= 5:
        return 'csv'
    
    # Log 检测 (包含时间戳或 ERROR/WARN/INFO)
    log_indicators = ['ERROR', 'WARN', 'INFO', 'DEBUG', r'\d{4}-\d{2}-\d{2}']
    log_matches = sum(1 for line in lines[:20] for ind in log_indicators if re.search(ind, line))
    if log_matches >= 3:
        return 'log'
    
    # Report 检测 (包含分隔线或标题)
    report_indicators = [r'^={10,}', r'^-{10,}', r'^\s*\|', r'Report', r'Summary']
    report_matches = sum(1 for line in lines[:30] for ind in report_indicators if re.search(ind, line))
    if report_matches >= 2:
        return 'report'
    
    return 'custom'


def _extract_patterns(lines: list[str]) -> list[PatternMatch]:
    """
    提取常见模式 (辅助信息)
    """
    pattern_counts = Counter()
    pattern_samples = {}
    
    for line in lines:
        for pattern, name in COMMON_PATTERNS:
            match = re.search(pattern, line)
            if match:
                pattern_counts[pattern] += 1
                if pattern not in pattern_samples:
                    pattern_samples[pattern] = line.strip()[:100]
    
    # 返回出现次数 >= 2 的模式
    results = []
    for pattern, count in pattern_counts.most_common(10):
        if count >= 2:
            results.append(PatternMatch(
                pattern=pattern,
                count=count,
                sample=pattern_samples.get(pattern, '')
            ))
    
    return results


def _extract_section_headers(lines: list[str]) -> list[str]:
    """
    提取段落标题
    """
    headers = []
    
    for i, line in enumerate(lines):
        # 检测全大写行 (可能是标题)
        if line.strip() and line.strip().isupper() and len(line.strip()) > 3:
            headers.append(line.strip())
        
        # 检测分隔线后的行 (可能是标题)
        if re.match(r'^[=\-]{10,}$', line.strip()):
            if i + 1 < len(lines) and lines[i + 1].strip():
                headers.append(lines[i + 1].strip())
        
        # 检测冒号结尾的行 (可能是标题)
        if line.strip().endswith(':') and len(line.strip()) < 50:
            headers.append(line.strip())
    
    # 去重并保持顺序
    seen = set()
    unique_headers = []
    for h in headers[:10]:
        if h not in seen:
            seen.add(h)
            unique_headers.append(h)
    
    return unique_headers


def _select_sample_lines(lines: list[str], max_samples: int = 20) -> list[str]:
    """
    选取代表性样本行
    """
    samples = []
    
    # 优先选择包含关键信息的行
    for line in lines:
        if len(samples) >= max_samples:
            break
        
        # 跳过空行和纯分隔线
        if not line.strip() or re.match(r'^[=\-\s]+$', line):
            continue
        
        # 优先选择包含模式的行
        has_pattern = any(re.search(p, line) for p, _ in COMMON_PATTERNS)
        
        if has_pattern or len(line.strip()) > 20:
            samples.append(line.strip()[:200])
    
    return samples


if __name__ == "__main__":
    # 测试用例
    import sys
    if len(sys.argv) > 1:
        analysis = read_files(sys.argv[1:])
        print(f"Files Analyzed: {analysis.files_analyzed}")
        print(f"Lines Sampled: {analysis.total_lines_sampled}")
        print(f"Detected Format: {analysis.detected_format}")
        print(f"Sample Lines ({len(analysis.sample_lines)}):")
        for line in analysis.sample_lines[:5]:
            print(f"  {line}")
