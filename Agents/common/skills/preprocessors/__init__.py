"""
Preprocessors Package

Preprocessors are executed unconditionally BEFORE LLM call.
They perform pure data extraction without semantic understanding.

Available Preprocessors:
- config_loader: Parse YAML config, detect checker type
- file_reader: Read file samples, detect format
- itemspec_parser: Parse ItemSpec JSON for CodeGen Agent
注意: 为避免循环导入，不在此处导出，由 agent.py 直接导入
"""

__all__ = []