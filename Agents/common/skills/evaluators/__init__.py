"""
evaluators 模块
===============
item_spec 评估、门禁、修复工具集

包含:
- ItemSpecGate: 在线门禁检查器
- ItemSpecRepairer: 定向修复器
- ItemSpecEvaluator: 离线评估器
"""

from .item_spec_gate import (
    ItemSpecGate,
    GateResult,
    GateFailure,
    GateLevel,
    FailureCode,
    check_item_spec,
)

from .item_spec_repairer import (
    ItemSpecRepairer,
    RepairResult,
    RepairAction,
    repair_item_spec,
)

from .item_spec_evaluator import (
    ItemSpecEvaluator,
    EvalReport,
    EvalMetrics,
    GoldSample,
    MatchResult,
    evaluate_item_spec,
    compare_models,
    create_gold_sample,
)

__all__ = [
    # Gate
    "ItemSpecGate",
    "GateResult",
    "GateFailure",
    "GateLevel",
    "FailureCode",
    "check_item_spec",
    # Repairer
    "ItemSpecRepairer",
    "RepairResult",
    "RepairAction",
    "repair_item_spec",
    # Evaluator
    "ItemSpecEvaluator",
    "EvalReport",
    "EvalMetrics",
    "GoldSample",
    "MatchResult",
    "evaluate_item_spec",
    "compare_models",
    "create_gold_sample",
]
