"""
Code Assembler - Postprocessor Skill for CodeGen Agent
"""
from .code_assembler import (
    assemble_checker_code,
    assemble_with_defaults,
    extract_method_body,
    merge_fragments
)

__all__ = [
    'assemble_checker_code',
    'assemble_with_defaults',
    'extract_method_body',
    'merge_fragments'
]
