"""
item_spec 定向修复器 (Repairer)
================================
在线主链路：基于 Gate 失败结果进行定向修复

修复策略:
- 只修失败点，不重写全部
- 最多 N 次迭代
- 每次迭代后重新检查

使用方式:
    from agents.common.skills.evaluators.item_spec_repairer import ItemSpecRepairer
    
    repairer = ItemSpecRepairer(llm_client=your_llm_client)
    result = await repairer.repair(item_spec_dict, gate_failures)
"""

import json
import re
import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from pathlib import Path

from .item_spec_gate import (
    ItemSpecGate,
    GateResult,
    GateFailure,
    GateLevel,
    FailureCode,
)


@dataclass
class RepairAction:
    """修复动作"""
    field_path: str
    action_type: str  # "set", "delete", "fix_regex", "add_field"
    old_value: Any
    new_value: Any
    reason: str


@dataclass
class RepairResult:
    """修复结果"""
    success: bool
    item_spec: dict
    iterations: int
    actions_taken: list = field(default_factory=list)  # List[RepairAction]
    final_gate_result: GateResult = None
    error_message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "iterations": self.iterations,
            "actions_taken": [
                {
                    "field_path": a.field_path,
                    "action_type": a.action_type,
                    "old_value": str(a.old_value)[:100] if a.old_value else None,
                    "new_value": str(a.new_value)[:100] if a.new_value else None,
                    "reason": a.reason
                }
                for a in self.actions_taken
            ],
            "final_gate_passed": self.final_gate_result.passed if self.final_gate_result else False,
            "error_message": self.error_message
        }


class ItemSpecRepairer:
    """item_spec 定向修复器"""
    
    MAX_ITERATIONS = 3  # 最大修复迭代次数
    
    # 可自动修复的失败代码
    AUTO_FIXABLE_CODES = {
        FailureCode.FIELD_MISSING,
        FailureCode.FIELD_TYPE_ERROR,
        FailureCode.REGEX_COMPILE_ERROR,
        FailureCode.EMPTY_REQUIRED,
    }
    
    # 默认值模板
    DEFAULT_VALUES = {
        "item_id": "UNKNOWN-0-0-0-00",
        "module": "UNKNOWN_MODULE",
        "description": "No description provided",
        "detected_type": 1,
        "check_logic": {
            "parsing_method": "Text-based log parsing",
            "regex_patterns": [".*"],
            "pass_fail_logic": "PASS if pattern found, FAIL otherwise"
        },
        "requirements": {"value": "N/A", "pattern_items": []},
        "waivers": {"value": "N/A", "waive_items": []},
        "pattern_items": [],
        "input_files": [],
    }
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_iterations: int = None,
        use_llm_for_regex: bool = True
    ):
        """
        Args:
            llm_client: LLM 客户端（用于复杂修复，如 regex）
            max_iterations: 最大迭代次数
            use_llm_for_regex: 是否使用 LLM 修复 regex 错误
        """
        self.llm_client = llm_client
        self.max_iterations = max_iterations or self.MAX_ITERATIONS
        self.use_llm_for_regex = use_llm_for_regex
        self.gate = ItemSpecGate()
    
    async def repair(
        self,
        item_spec: dict,
        initial_failures: list[GateFailure] = None
    ) -> RepairResult:
        """
        执行定向修复
        
        Args:
            item_spec: 原始 item_spec
            initial_failures: 初始失败列表（可选，如果不提供会重新检查）
            
        Returns:
            RepairResult: 修复结果
        """
        spec = copy.deepcopy(item_spec)
        all_actions = []
        
        for iteration in range(self.max_iterations):
            # 检查当前状态
            if initial_failures and iteration == 0:
                failures = initial_failures
            else:
                gate_result = self.gate.check(spec)
                if gate_result.passed:
                    return RepairResult(
                        success=True,
                        item_spec=spec,
                        iterations=iteration,
                        actions_taken=all_actions,
                        final_gate_result=gate_result
                    )
                failures = gate_result.failures
            
            # 按优先级修复（L0 先于 L1）
            l0_failures = [f for f in failures if f.level == GateLevel.L0_STRUCTURE]
            l1_failures = [f for f in failures if f.level == GateLevel.L1_EXECUTABLE]
            
            actions_this_round = []
            
            # 修复 L0 问题
            for failure in l0_failures:
                action = await self._fix_failure(spec, failure)
                if action:
                    actions_this_round.append(action)
                    self._apply_action(spec, action)
            
            # 如果 L0 都修完了，修复 L1
            if not l0_failures:
                for failure in l1_failures:
                    action = await self._fix_failure(spec, failure)
                    if action:
                        actions_this_round.append(action)
                        self._apply_action(spec, action)
            
            all_actions.extend(actions_this_round)
            
            # 如果这轮没有任何修复动作，说明无法继续
            if not actions_this_round:
                break
        
        # 最终检查
        final_result = self.gate.check(spec)
        
        return RepairResult(
            success=final_result.passed,
            item_spec=spec,
            iterations=self.max_iterations,
            actions_taken=all_actions,
            final_gate_result=final_result,
            error_message="" if final_result.passed else "达到最大迭代次数仍未完全修复"
        )
    
    async def _fix_failure(self, spec: dict, failure: GateFailure) -> Optional[RepairAction]:
        """修复单个失败"""
        
        if failure.code == FailureCode.FIELD_MISSING:
            return self._fix_missing_field(spec, failure)
        
        elif failure.code == FailureCode.FIELD_TYPE_ERROR:
            return self._fix_type_error(spec, failure)
        
        elif failure.code == FailureCode.REGEX_COMPILE_ERROR:
            return await self._fix_regex_error(spec, failure)
        
        elif failure.code == FailureCode.EMPTY_REQUIRED:
            return self._fix_empty_required(spec, failure)
        
        elif failure.code == FailureCode.ENUM_INVALID:
            return self._fix_enum_invalid(spec, failure)
        
        elif failure.code == FailureCode.REGEX_TIMEOUT_RISK:
            return await self._fix_regex_timeout(spec, failure)
        
        return None
    
    def _fix_missing_field(self, spec: dict, failure: GateFailure) -> RepairAction:
        """修复缺失字段"""
        field_path = failure.field_path
        parts = field_path.split(".")
        
        # 获取默认值
        if len(parts) == 1:
            default_value = self.DEFAULT_VALUES.get(parts[0], "")
        elif len(parts) == 2 and parts[0] == "check_logic":
            default_value = self.DEFAULT_VALUES.get("check_logic", {}).get(parts[1], "")
        else:
            default_value = ""
        
        return RepairAction(
            field_path=field_path,
            action_type="add_field",
            old_value=None,
            new_value=default_value,
            reason=f"添加缺失字段 '{field_path}'"
        )
    
    def _fix_type_error(self, spec: dict, failure: GateFailure) -> RepairAction:
        """修复类型错误"""
        field_path = failure.field_path
        old_value = failure.value
        
        # 尝试类型转换
        expected_types = {
            "item_id": str,
            "module": str,
            "description": str,
            "detected_type": int,
            "check_logic": dict,
            "check_logic.parsing_method": str,
            "check_logic.regex_patterns": list,
            "check_logic.pass_fail_logic": str,
        }
        
        expected_type = expected_types.get(field_path)
        
        if expected_type == int and isinstance(old_value, str):
            try:
                new_value = int(old_value)
            except ValueError:
                new_value = 1  # 默认值
        elif expected_type == str:
            new_value = str(old_value)
        elif expected_type == list and isinstance(old_value, str):
            new_value = [old_value]
        elif expected_type == dict and old_value is None:
            new_value = {}
        else:
            new_value = self.DEFAULT_VALUES.get(field_path.split(".")[0], "")
        
        return RepairAction(
            field_path=field_path,
            action_type="set",
            old_value=old_value,
            new_value=new_value,
            reason=f"修复类型错误: {type(old_value).__name__} -> {expected_type.__name__ if expected_type else 'unknown'}"
        )
    
    async def _fix_regex_error(self, spec: dict, failure: GateFailure) -> Optional[RepairAction]:
        """修复 regex 编译错误"""
        old_pattern = failure.value
        field_path = failure.field_path
        
        # 提取索引
        match = re.search(r'\[(\d+)\]', field_path)
        if not match:
            return None
        index = int(match.group(1))
        
        # 尝试自动修复常见错误
        new_pattern = self._auto_fix_regex(old_pattern)
        
        # 如果自动修复失败且有 LLM，使用 LLM
        if new_pattern is None and self.llm_client and self.use_llm_for_regex:
            new_pattern = await self._llm_fix_regex(old_pattern, str(failure.message))
        
        # 如果还是失败，使用通配符替代
        if new_pattern is None:
            new_pattern = ".*"  # 匹配所有，最保守的降级
        
        return RepairAction(
            field_path=field_path,
            action_type="fix_regex",
            old_value=old_pattern,
            new_value=new_pattern,
            reason=f"修复 regex 编译错误"
        )
    
    def _auto_fix_regex(self, pattern: str) -> Optional[str]:
        """自动修复常见 regex 错误"""
        if not isinstance(pattern, str):
            return None
        
        fixed = pattern
        
        # 1. 转义未闭合的括号
        open_parens = fixed.count('(') - fixed.count('\\(')
        close_parens = fixed.count(')') - fixed.count('\\)')
        if open_parens > close_parens:
            fixed += ')' * (open_parens - close_parens)
        elif close_parens > open_parens:
            fixed = '(' * (close_parens - open_parens) + fixed
        
        # 2. 转义未闭合的方括号
        open_brackets = fixed.count('[') - fixed.count('\\[')
        close_brackets = fixed.count(']') - fixed.count('\\]')
        if open_brackets > close_brackets:
            fixed += ']' * (open_brackets - close_brackets)
        
        # 3. 修复空的字符类 []
        fixed = re.sub(r'\[\]', '[^]', fixed)  # 空字符类 -> 任意字符
        
        # 4. 修复 \s+ 后面紧跟量词的问题
        fixed = re.sub(r'\+\+', '+', fixed)
        fixed = re.sub(r'\*\*', '*', fixed)
        
        # 5. 验证修复结果
        try:
            re.compile(fixed)
            return fixed
        except re.error:
            return None
    
    async def _llm_fix_regex(self, pattern: str, error_msg: str) -> Optional[str]:
        """使用 LLM 修复 regex"""
        if not self.llm_client:
            return None
        
        prompt = f"""修复以下正则表达式的语法错误:

原始正则: {pattern}
错误信息: {error_msg}

请只返回修复后的正则表达式，不要任何解释。如果无法修复，返回 .*"""
        
        try:
            # 假设 llm_client 有 chat 或 complete 方法
            if hasattr(self.llm_client, 'chat'):
                response = await self.llm_client.chat(prompt)
            elif hasattr(self.llm_client, 'complete'):
                response = await self.llm_client.complete(prompt)
            else:
                return None
            
            fixed = response.strip()
            # 验证
            re.compile(fixed)
            return fixed
        except Exception:
            return None
    
    async def _fix_regex_timeout(self, spec: dict, failure: GateFailure) -> Optional[RepairAction]:
        """修复 regex 超时风险"""
        old_pattern = failure.value
        field_path = failure.field_path
        
        # 简化策略：移除嵌套量词
        new_pattern = old_pattern
        
        # 移除 (...)+ 中的内部量词
        new_pattern = re.sub(r'\(\.\*\+\)\+', '(.+)', new_pattern)
        new_pattern = re.sub(r'\(\.\*\)\+', '(.*)', new_pattern)
        
        # 限制开放式通配
        new_pattern = re.sub(r'\.\*(?!\?)', '.*?', new_pattern)  # 改为非贪婪
        
        return RepairAction(
            field_path=field_path,
            action_type="fix_regex",
            old_value=old_pattern,
            new_value=new_pattern,
            reason="简化 regex 以避免超时风险"
        )
    
    def _fix_empty_required(self, spec: dict, failure: GateFailure) -> RepairAction:
        """修复空的必填字段"""
        field_path = failure.field_path
        
        if "regex_patterns" in field_path:
            # 添加一个通用的 regex
            new_value = [".*"]
        else:
            new_value = ["placeholder"]
        
        return RepairAction(
            field_path=field_path,
            action_type="set",
            old_value=[],
            new_value=new_value,
            reason="填充空的必填列表"
        )
    
    def _fix_enum_invalid(self, spec: dict, failure: GateFailure) -> RepairAction:
        """修复无效枚举值"""
        field_path = failure.field_path
        
        if field_path == "detected_type":
            # 默认为 Type 1
            return RepairAction(
                field_path=field_path,
                action_type="set",
                old_value=failure.value,
                new_value=1,
                reason="将无效的 detected_type 修正为默认值 1"
            )
        
        return None
    
    def _apply_action(self, spec: dict, action: RepairAction):
        """应用修复动作到 spec"""
        parts = action.field_path.split(".")
        
        # 处理数组索引
        def parse_path_part(part):
            match = re.match(r'(\w+)\[(\d+)\]', part)
            if match:
                return match.group(1), int(match.group(2))
            return part, None
        
        # 导航到目标位置
        current = spec
        for i, part in enumerate(parts[:-1]):
            key, index = parse_path_part(part)
            if key not in current:
                current[key] = {} if index is None else []
            current = current[key]
            if index is not None:
                while len(current) <= index:
                    current.append(None)
                if current[index] is None:
                    current[index] = {}
                current = current[index]
        
        # 设置值
        last_part = parts[-1]
        key, index = parse_path_part(last_part)
        
        if action.action_type in ("set", "add_field", "fix_regex"):
            if index is not None:
                if key not in current:
                    current[key] = []
                while len(current[key]) <= index:
                    current[key].append(None)
                current[key][index] = action.new_value
            else:
                current[key] = action.new_value
        elif action.action_type == "delete":
            if key in current:
                del current[key]


# 便捷函数
async def repair_item_spec(
    item_spec: dict,
    llm_client: Any = None,
    max_iterations: int = 3
) -> RepairResult:
    """
    便捷函数：修复 item_spec
    
    Args:
        item_spec: 原始 item_spec
        llm_client: LLM 客户端（可选）
        max_iterations: 最大迭代次数
        
    Returns:
        RepairResult: 修复结果
    """
    repairer = ItemSpecRepairer(
        llm_client=llm_client,
        max_iterations=max_iterations
    )
    return await repairer.repair(item_spec)
