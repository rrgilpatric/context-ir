"""Tool-facing facade over repository analysis and semantic compilation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from context_ir.analyzer import analyze_repository
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_types import (
    ResolverDiagnostic,
    SemanticCompileResult,
    SemanticOptimizationWarning,
    SemanticProgram,
    SemanticSelectionRecord,
    SyntaxDiagnostic,
    UnresolvedAccess,
    UnsupportedConstruct,
)

EmbeddingFunction: TypeAlias = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class SemanticContextRequest:
    """Inputs for compiling one repository context request."""

    repo_root: Path | str
    query: str
    budget: int
    embed_fn: EmbeddingFunction | None = None


@dataclass(frozen=True)
class SemanticContextResponse:
    """Transparent tool-facing result for semantic repository compilation."""

    program: SemanticProgram
    compile_result: SemanticCompileResult
    unresolved_frontier: tuple[UnresolvedAccess, ...]
    unsupported_constructs: tuple[UnsupportedConstruct, ...]
    syntax_diagnostics: tuple[SyntaxDiagnostic, ...]
    semantic_diagnostics: tuple[ResolverDiagnostic, ...]
    optimization_warnings: tuple[SemanticOptimizationWarning, ...]
    selection_trace: tuple[SemanticSelectionRecord, ...]
    omitted_unit_ids: tuple[str, ...]
    compile_total_tokens: int
    compile_budget: int

    def __post_init__(self) -> None:
        """Reject facade surfaces that diverge from the underlying results."""
        if self.unresolved_frontier != tuple(self.program.unresolved_frontier):
            raise ValueError("unresolved_frontier must mirror SemanticProgram")
        if self.unsupported_constructs != tuple(self.program.unsupported_constructs):
            raise ValueError("unsupported_constructs must mirror SemanticProgram")
        if self.syntax_diagnostics != tuple(self.program.syntax.diagnostics):
            raise ValueError("syntax_diagnostics must mirror SemanticProgram.syntax")
        if self.semantic_diagnostics != tuple(self.program.diagnostics):
            raise ValueError("semantic_diagnostics must mirror SemanticProgram")
        if self.optimization_warnings != self.compile_result.optimization.warnings:
            raise ValueError("optimization_warnings must mirror compile_result")
        if self.selection_trace != self.compile_result.optimization.selections:
            raise ValueError("selection_trace must mirror compile_result")
        if self.omitted_unit_ids != self.compile_result.omitted_unit_ids:
            raise ValueError("omitted_unit_ids must mirror compile_result")
        if self.compile_total_tokens != self.compile_result.total_tokens:
            raise ValueError("compile_total_tokens must mirror compile_result")
        if self.compile_budget != self.compile_result.budget:
            raise ValueError("compile_budget must mirror compile_result")


def compile_repository_context(
    request: SemanticContextRequest,
) -> SemanticContextResponse:
    """Analyze a repository and compile a semantic context response."""
    program = analyze_repository(request.repo_root)
    compile_result = compile_semantic_context(
        program,
        request.query,
        request.budget,
        embed_fn=request.embed_fn,
    )
    return SemanticContextResponse(
        program=program,
        compile_result=compile_result,
        unresolved_frontier=tuple(program.unresolved_frontier),
        unsupported_constructs=tuple(program.unsupported_constructs),
        syntax_diagnostics=tuple(program.syntax.diagnostics),
        semantic_diagnostics=tuple(program.diagnostics),
        optimization_warnings=compile_result.optimization.warnings,
        selection_trace=compile_result.optimization.selections,
        omitted_unit_ids=compile_result.omitted_unit_ids,
        compile_total_tokens=compile_result.total_tokens,
        compile_budget=compile_result.budget,
    )


__all__ = [
    "EmbeddingFunction",
    "SemanticContextRequest",
    "SemanticContextResponse",
    "compile_repository_context",
]
