"""
item_spec 离线评估器 (Evaluator)
=================================
离线评估链路：计算质量分数、生成评估报告

评估指标:
- L0 schema_pass_rate: Schema 通过率（应为 100%）
- L1 regex_compile_rate: Regex 编译通过率
- L1 regex_timeout_rate: Regex 超时率
- L2 match_rate: 正样本匹配率（需要 Gold 数据）
- L2 false_positive_rate: 负样本误匹配率（需要 Gold 数据）

使用方式:
    from agents.common.skills.evaluators.item_spec_evaluator import ItemSpecEvaluator
    
    evaluator = ItemSpecEvaluator()
    report = evaluator.evaluate(item_spec, gold_samples=gold_data)
"""

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


@dataclass
class GoldSample:
    """黄金标准样本"""
    sample_id: str
    log_content: str  # 日志内容
    should_match: bool  # 是否应该匹配（正样本 True，负样本 False）
    expected_extracts: dict = field(default_factory=dict)  # 期望提取的字段
    item_type: int = 1  # 对应的 detected_type
    description: str = ""


@dataclass
class MatchResult:
    """匹配结果"""
    sample_id: str
    should_match: bool
    actually_matched: bool
    is_correct: bool
    matched_pattern: str = ""
    extracted_values: dict = field(default_factory=dict)
    extraction_correct: bool = True


@dataclass
class EvalMetrics:
    """评估指标"""
    # L0 指标
    schema_pass_rate: float = 0.0
    field_completeness: float = 0.0
    
    # L1 指标
    regex_compile_rate: float = 0.0
    regex_timeout_rate: float = 0.0
    regex_quality_score: float = 0.0  # 综合分
    
    # L2 指标（需要 Gold）
    match_rate: float = 0.0  # 正样本匹配率 (Recall)
    false_positive_rate: float = 0.0  # 负样本误匹配率
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    extraction_accuracy: float = 0.0  # 字段提取准确率
    
    # 综合分
    overall_score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "L0_schema_pass_rate": self.schema_pass_rate,
            "L0_field_completeness": self.field_completeness,
            "L1_regex_compile_rate": self.regex_compile_rate,
            "L1_regex_timeout_rate": self.regex_timeout_rate,
            "L1_regex_quality_score": self.regex_quality_score,
            "L2_match_rate": self.match_rate,
            "L2_false_positive_rate": self.false_positive_rate,
            "L2_precision": self.precision,
            "L2_recall": self.recall,
            "L2_f1_score": self.f1_score,
            "L2_extraction_accuracy": self.extraction_accuracy,
            "overall_score": self.overall_score,
        }


@dataclass
class EvalReport:
    """评估报告"""
    item_id: str
    model_name: str
    timestamp: str
    metrics: EvalMetrics
    match_details: list = field(default_factory=list)  # List[MatchResult]
    gate_failures: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    eval_duration_ms: float = 0
    
    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "model_name": self.model_name,
            "timestamp": self.timestamp,
            "metrics": self.metrics.to_dict(),
            "match_details": [
                {
                    "sample_id": m.sample_id,
                    "should_match": m.should_match,
                    "actually_matched": m.actually_matched,
                    "is_correct": m.is_correct,
                    "matched_pattern": m.matched_pattern,
                    "extracted_values": m.extracted_values,
                }
                for m in self.match_details
            ],
            "gate_failures_count": len(self.gate_failures),
            "warnings": self.warnings,
            "eval_duration_ms": self.eval_duration_ms,
        }
    
    def to_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            f"# Evaluation Report: {self.item_id}",
            f"",
            f"**Model**: {self.model_name}",
            f"**Timestamp**: {self.timestamp}",
            f"**Duration**: {self.eval_duration_ms:.1f}ms",
            f"",
            f"## Overall Score: {self.metrics.overall_score:.1%}",
            f"",
            f"## L0 - Structure Metrics",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| Schema Pass Rate | {self.metrics.schema_pass_rate:.1%} |",
            f"| Field Completeness | {self.metrics.field_completeness:.1%} |",
            f"",
            f"## L1 - Executable Metrics",
            f"| Metric | Score |",
            f"|--------|-------|",
            f"| Regex Compile Rate | {self.metrics.regex_compile_rate:.1%} |",
            f"| Regex Timeout Rate | {self.metrics.regex_timeout_rate:.1%} |",
            f"| Regex Quality Score | {self.metrics.regex_quality_score:.1%} |",
            f"",
        ]
        
        if self.match_details:
            lines.extend([
                f"## L2 - Matching Metrics",
                f"| Metric | Score |",
                f"|--------|-------|",
                f"| Match Rate (Recall) | {self.metrics.match_rate:.1%} |",
                f"| False Positive Rate | {self.metrics.false_positive_rate:.1%} |",
                f"| Precision | {self.metrics.precision:.1%} |",
                f"| F1 Score | {self.metrics.f1_score:.1%} |",
                f"| Extraction Accuracy | {self.metrics.extraction_accuracy:.1%} |",
                f"",
                f"## Match Details",
                f"| Sample | Should Match | Actually Matched | Correct |",
                f"|--------|--------------|------------------|---------|",
            ])
            for m in self.match_details:
                lines.append(
                    f"| {m.sample_id} | {m.should_match} | {m.actually_matched} | {'✓' if m.is_correct else '✗'} |"
                )
        
        if self.warnings:
            lines.extend([
                f"",
                f"## Warnings",
            ])
            for w in self.warnings:
                lines.append(f"- {w}")
        
        return "\n".join(lines)


class ItemSpecEvaluator:
    """item_spec 离线评估器"""
    
    # 必填字段列表（用于计算完整性）
    REQUIRED_FIELDS = [
        "item_id", "module", "description", "detected_type",
        "check_logic", "check_logic.parsing_method",
        "check_logic.regex_patterns", "check_logic.pass_fail_logic"
    ]
    
    OPTIONAL_FIELDS = [
        "requirements", "waivers", "input_files", "file_analysis",
        "type_examples", "generated_readme", "parse_logic",
        "type_execution_specs", "test_scenarios",
        "output_info01_format", "output_error01_format"
    ]
    
    def __init__(self, regex_timeout_ms: int = 100):
        """
        Args:
            regex_timeout_ms: Regex 超时阈值（毫秒）
        """
        self.regex_timeout_ms = regex_timeout_ms
    
    def evaluate(
        self,
        item_spec: dict | str | Path,
        gold_samples: list[GoldSample] = None,
        model_name: str = "unknown"
    ) -> EvalReport:
        """
        执行离线评估
        
        Args:
            item_spec: item_spec 字典、JSON 字符串或文件路径
            gold_samples: 黄金标准样本（可选）
            model_name: 生成该 spec 的模型名称
            
        Returns:
            EvalReport: 评估报告
        """
        start_time = time.perf_counter()
        
        # 解析输入
        spec = self._parse_input(item_spec)
        if spec is None:
            return self._create_error_report("Invalid input", model_name)
        
        item_id = spec.get("item_id", "UNKNOWN")
        metrics = EvalMetrics()
        warnings = []
        match_details = []
        
        # L0 评估
        l0_metrics = self._evaluate_l0(spec)
        metrics.schema_pass_rate = l0_metrics["schema_pass_rate"]
        metrics.field_completeness = l0_metrics["field_completeness"]
        
        # L1 评估
        l1_metrics, l1_warnings = self._evaluate_l1(spec)
        metrics.regex_compile_rate = l1_metrics["compile_rate"]
        metrics.regex_timeout_rate = l1_metrics["timeout_rate"]
        metrics.regex_quality_score = l1_metrics["quality_score"]
        warnings.extend(l1_warnings)
        
        # L2 评估（如果有 Gold 数据）
        if gold_samples:
            l2_metrics, match_details = self._evaluate_l2(spec, gold_samples)
            metrics.match_rate = l2_metrics["match_rate"]
            metrics.false_positive_rate = l2_metrics["false_positive_rate"]
            metrics.precision = l2_metrics["precision"]
            metrics.recall = l2_metrics["recall"]
            metrics.f1_score = l2_metrics["f1_score"]
            metrics.extraction_accuracy = l2_metrics["extraction_accuracy"]
        
        # 计算综合分
        metrics.overall_score = self._calculate_overall_score(metrics, has_gold=bool(gold_samples))
        
        return EvalReport(
            item_id=item_id,
            model_name=model_name,
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            match_details=match_details,
            warnings=warnings,
            eval_duration_ms=(time.perf_counter() - start_time) * 1000
        )
    
    def _parse_input(self, item_spec) -> Optional[dict]:
        """解析输入"""
        if isinstance(item_spec, dict):
            return item_spec
        
        if isinstance(item_spec, (str, Path)):
            path = Path(item_spec)
            if path.exists() and path.suffix == '.json':
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    return None
            elif isinstance(item_spec, str):
                try:
                    return json.loads(item_spec)
                except Exception:
                    return None
        
        return None
    
    def _evaluate_l0(self, spec: dict) -> dict:
        """L0 结构评估"""
        # Schema 通过率（简化：检查必填字段）
        required_present = 0
        for field_path in self.REQUIRED_FIELDS:
            parts = field_path.split(".")
            current = spec
            found = True
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    found = False
                    break
            if found:
                required_present += 1
        
        schema_pass_rate = required_present / len(self.REQUIRED_FIELDS)
        
        # 字段完整性（包括可选字段）
        all_fields = self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS
        total_present = required_present
        for field_path in self.OPTIONAL_FIELDS:
            parts = field_path.split(".")
            current = spec
            found = True
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    found = False
                    break
            if found:
                total_present += 1
        
        field_completeness = total_present / len(all_fields)
        
        return {
            "schema_pass_rate": schema_pass_rate,
            "field_completeness": field_completeness,
        }
    
    def _evaluate_l1(self, spec: dict) -> tuple[dict, list]:
        """L1 可执行评估"""
        warnings = []
        
        check_logic = spec.get("check_logic", {})
        patterns = check_logic.get("regex_patterns", [])
        
        if not patterns:
            return {
                "compile_rate": 0.0,
                "timeout_rate": 0.0,
                "quality_score": 0.0,
            }, ["No regex patterns found"]
        
        compile_success = 0
        timeout_count = 0
        
        test_string = "a" * 10000 + " ERROR: test message " + "b" * 10000
        
        for pattern in patterns:
            if not isinstance(pattern, str):
                continue
            
            # 编译测试
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                compile_success += 1
            except re.error as e:
                warnings.append(f"Regex compile error: {pattern[:50]}... - {e}")
                continue
            
            # 超时测试
            start = time.perf_counter()
            try:
                compiled.search(test_string)
            except Exception:
                pass
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            if elapsed_ms > self.regex_timeout_ms:
                timeout_count += 1
                warnings.append(f"Regex slow: {pattern[:50]}... - {elapsed_ms:.1f}ms")
        
        total = len([p for p in patterns if isinstance(p, str)])
        compile_rate = compile_success / total if total > 0 else 0
        timeout_rate = timeout_count / total if total > 0 else 0
        
        # 质量分 = 编译率 * (1 - 超时率)
        quality_score = compile_rate * (1 - timeout_rate)
        
        return {
            "compile_rate": compile_rate,
            "timeout_rate": timeout_rate,
            "quality_score": quality_score,
        }, warnings
    
    def _evaluate_l2(
        self,
        spec: dict,
        gold_samples: list[GoldSample]
    ) -> tuple[dict, list[MatchResult]]:
        """L2 匹配评估"""
        check_logic = spec.get("check_logic", {})
        patterns = check_logic.get("regex_patterns", [])
        
        # 编译所有有效的 regex
        compiled_patterns = []
        for pattern in patterns:
            if isinstance(pattern, str):
                try:
                    compiled_patterns.append((pattern, re.compile(pattern, re.IGNORECASE)))
                except re.error:
                    pass
        
        if not compiled_patterns:
            return {
                "match_rate": 0.0,
                "false_positive_rate": 1.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "extraction_accuracy": 0.0,
            }, []
        
        match_results = []
        
        # 统计
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        extraction_correct_count = 0
        extraction_total = 0
        
        for sample in gold_samples:
            actually_matched = False
            matched_pattern = ""
            extracted_values = {}
            
            # 尝试每个 pattern
            for pattern_str, compiled in compiled_patterns:
                match = compiled.search(sample.log_content)
                if match:
                    actually_matched = True
                    matched_pattern = pattern_str
                    # 提取 named groups
                    extracted_values = match.groupdict()
                    break
            
            # 判断是否正确
            is_correct = (sample.should_match == actually_matched)
            
            # 检查提取准确性
            extraction_correct = True
            if sample.should_match and sample.expected_extracts:
                extraction_total += 1
                for key, expected_value in sample.expected_extracts.items():
                    if key not in extracted_values or extracted_values[key] != expected_value:
                        extraction_correct = False
                        break
                if extraction_correct:
                    extraction_correct_count += 1
            
            # 更新统计
            if sample.should_match:
                if actually_matched:
                    true_positives += 1
                else:
                    false_negatives += 1
            else:
                if actually_matched:
                    false_positives += 1
                else:
                    true_negatives += 1
            
            match_results.append(MatchResult(
                sample_id=sample.sample_id,
                should_match=sample.should_match,
                actually_matched=actually_matched,
                is_correct=is_correct,
                matched_pattern=matched_pattern,
                extracted_values=extracted_values,
                extraction_correct=extraction_correct,
            ))
        
        # 计算指标
        positive_samples = sum(1 for s in gold_samples if s.should_match)
        negative_samples = len(gold_samples) - positive_samples
        
        match_rate = true_positives / positive_samples if positive_samples > 0 else 0
        false_positive_rate = false_positives / negative_samples if negative_samples > 0 else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = match_rate
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        extraction_accuracy = extraction_correct_count / extraction_total if extraction_total > 0 else 1.0
        
        return {
            "match_rate": match_rate,
            "false_positive_rate": false_positive_rate,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "extraction_accuracy": extraction_accuracy,
        }, match_results
    
    def _calculate_overall_score(self, metrics: EvalMetrics, has_gold: bool) -> float:
        """计算综合分"""
        # 权重配置
        if has_gold:
            # 有 Gold 数据时，L2 权重更高
            weights = {
                "l0": 0.2,  # L0 占 20%
                "l1": 0.3,  # L1 占 30%
                "l2": 0.5,  # L2 占 50%
            }
            l0_score = (metrics.schema_pass_rate + metrics.field_completeness) / 2
            l1_score = metrics.regex_quality_score
            l2_score = metrics.f1_score
            
            return (
                weights["l0"] * l0_score +
                weights["l1"] * l1_score +
                weights["l2"] * l2_score
            )
        else:
            # 无 Gold 数据时，只看 L0/L1
            weights = {
                "l0": 0.4,
                "l1": 0.6,
            }
            l0_score = (metrics.schema_pass_rate + metrics.field_completeness) / 2
            l1_score = metrics.regex_quality_score
            
            return (
                weights["l0"] * l0_score +
                weights["l1"] * l1_score
            )
    
    def _create_error_report(self, error_msg: str, model_name: str) -> EvalReport:
        """创建错误报告"""
        return EvalReport(
            item_id="ERROR",
            model_name=model_name,
            timestamp=datetime.now().isoformat(),
            metrics=EvalMetrics(),
            warnings=[error_msg],
        )


def compare_models(
    spec_paths: dict[str, str | Path],
    gold_samples: list[GoldSample] = None
) -> dict:
    """
    比较多个模型生成的 item_spec
    
    Args:
        spec_paths: {model_name: spec_path} 字典
        gold_samples: 黄金标准样本
        
    Returns:
        比较报告
    """
    evaluator = ItemSpecEvaluator()
    reports = {}
    
    for model_name, spec_path in spec_paths.items():
        report = evaluator.evaluate(spec_path, gold_samples, model_name)
        reports[model_name] = report
    
    # 生成比较表格
    comparison = {
        "models": list(reports.keys()),
        "metrics_comparison": {},
        "winner": None,
        "reports": {name: r.to_dict() for name, r in reports.items()}
    }
    
    # 比较各项指标
    metric_names = [
        "schema_pass_rate", "field_completeness",
        "regex_compile_rate", "regex_quality_score",
        "f1_score", "overall_score"
    ]
    
    for metric in metric_names:
        comparison["metrics_comparison"][metric] = {
            name: getattr(r.metrics, metric)
            for name, r in reports.items()
        }
    
    # 选出综合分最高的
    if reports:
        winner = max(reports.keys(), key=lambda k: reports[k].metrics.overall_score)
        comparison["winner"] = winner
    
    return comparison


# 便捷函数
def evaluate_item_spec(
    item_spec: dict | str | Path,
    gold_samples: list[GoldSample] = None,
    model_name: str = "unknown"
) -> EvalReport:
    """
    便捷函数：评估 item_spec
    """
    evaluator = ItemSpecEvaluator()
    return evaluator.evaluate(item_spec, gold_samples, model_name)


def create_gold_sample(
    sample_id: str,
    log_content: str,
    should_match: bool,
    expected_extracts: dict = None,
    item_type: int = 1,
    description: str = ""
) -> GoldSample:
    """便捷函数：创建 Gold 样本"""
    return GoldSample(
        sample_id=sample_id,
        log_content=log_content,
        should_match=should_match,
        expected_extracts=expected_extracts or {},
        item_type=item_type,
        description=description
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        
        report = evaluate_item_spec(path, model_name=model)
        print(report.to_markdown())
    else:
        print("Usage: python item_spec_evaluator.py <path_to_item_spec.json> [model_name]")
