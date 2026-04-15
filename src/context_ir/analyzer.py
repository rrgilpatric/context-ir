"""Public semantic repository analysis orchestration."""

from __future__ import annotations

from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.semantic_types import SemanticProgram


def analyze_repository(repo_root: Path | str) -> SemanticProgram:
    """Analyze ``repo_root`` into the fully derived semantic program."""
    syntax = extract_syntax(repo_root)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    return derive_dependency_frontier(resolved_program)


__all__ = ["analyze_repository"]
