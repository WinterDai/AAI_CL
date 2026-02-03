"""
Postprocessors Package

Postprocessors are executed unconditionally AFTER LLM call.
They perform deterministic rendering without business logic.

Available Postprocessors:
- readme_renderer: Jinja2 template rendering
- json_validator: Rule-based validation
- itemspec_builder: Assemble ItemSpec for downstream
- code_assembler: Assemble Checker code from templates + LLM fragments
- code_formatter: Format Python code with black/isort
注意: 为避免循环导入，不在此处导出，由 agent.py 直接导入
"""

__all__ = []