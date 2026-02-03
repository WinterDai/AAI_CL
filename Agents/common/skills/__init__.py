"""
Common Skills Package

Preprocessors, Postprocessors, and Tools for all Agents.
Following Claude Cookbook SKILL.md format.

Directory Structure:
├── preprocessors/     - Unconditional execution BEFORE LLM (data extraction)
├── postprocessors/    - Unconditional execution AFTER LLM (deterministic rendering)
└── tools/             - LLM decides whether to call (external interaction)
"""

from pathlib import Path

SKILLS_ROOT = Path(__file__).parent

__all__ = ['SKILLS_ROOT']
