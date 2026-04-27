"""Tool-facing facade over repository analysis and semantic compilation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, TypedDict

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

if TYPE_CHECKING:
    from context_ir.runtime_acquisition import (
        DelattrRuntimeObservation,
        DirRuntimeObservation,
        DynamicImportRuntimeObservation,
        EvalRuntimeObservation,
        GetattrRuntimeObservation,
        GlobalsRuntimeObservation,
        HasattrRuntimeObservation,
        LocalsRuntimeObservation,
        MetaclassBehaviorRuntimeObservation,
        SetattrRuntimeObservation,
        VarsRuntimeObservation,
    )

EmbeddingFunction: TypeAlias = Callable[[list[str]], list[list[float]]]


class _AnalyzeRepositoryKwargs(TypedDict, total=False):
    """Optional runtime-observation kwargs accepted by ``analyze_repository``."""

    delattr_runtime_observations: Sequence[DelattrRuntimeObservation]
    dynamic_import_runtime_observations: Sequence[DynamicImportRuntimeObservation]
    dir_runtime_observations: Sequence[DirRuntimeObservation]
    eval_runtime_observations: Sequence[EvalRuntimeObservation]
    getattr_runtime_observations: Sequence[GetattrRuntimeObservation]
    globals_runtime_observations: Sequence[GlobalsRuntimeObservation]
    hasattr_runtime_observations: Sequence[HasattrRuntimeObservation]
    locals_runtime_observations: Sequence[LocalsRuntimeObservation]
    metaclass_behavior_runtime_observations: Sequence[
        MetaclassBehaviorRuntimeObservation
    ]
    setattr_runtime_observations: Sequence[SetattrRuntimeObservation]
    vars_runtime_observations: Sequence[VarsRuntimeObservation]


@dataclass(frozen=True)
class SemanticContextRequest:
    """Inputs for compiling one repository context request."""

    repo_root: Path | str
    query: str
    budget: int
    embed_fn: EmbeddingFunction | None = None
    dynamic_import_runtime_observations: (
        Sequence[DynamicImportRuntimeObservation] | None
    ) = None
    eval_runtime_observations: Sequence[EvalRuntimeObservation] | None = None
    hasattr_runtime_observations: Sequence[HasattrRuntimeObservation] | None = None
    getattr_runtime_observations: Sequence[GetattrRuntimeObservation] | None = None
    vars_runtime_observations: Sequence[VarsRuntimeObservation] | None = None
    globals_runtime_observations: Sequence[GlobalsRuntimeObservation] | None = None
    locals_runtime_observations: Sequence[LocalsRuntimeObservation] | None = None
    metaclass_behavior_runtime_observations: (
        Sequence[MetaclassBehaviorRuntimeObservation] | None
    ) = None
    setattr_runtime_observations: Sequence[SetattrRuntimeObservation] | None = None
    delattr_runtime_observations: Sequence[DelattrRuntimeObservation] | None = None
    dir_runtime_observations: Sequence[DirRuntimeObservation] | None = None


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
    dynamic_import_runtime_observations = request.dynamic_import_runtime_observations
    eval_runtime_observations = request.eval_runtime_observations
    hasattr_runtime_observations = request.hasattr_runtime_observations
    getattr_runtime_observations = request.getattr_runtime_observations
    vars_runtime_observations = request.vars_runtime_observations
    globals_runtime_observations = request.globals_runtime_observations
    locals_runtime_observations = request.locals_runtime_observations
    metaclass_behavior_runtime_observations = (
        request.metaclass_behavior_runtime_observations
    )
    setattr_runtime_observations = request.setattr_runtime_observations
    delattr_runtime_observations = request.delattr_runtime_observations
    dir_runtime_observations = request.dir_runtime_observations

    analyze_kwargs: _AnalyzeRepositoryKwargs = {}
    if delattr_runtime_observations is not None:
        analyze_kwargs["delattr_runtime_observations"] = delattr_runtime_observations
    if dynamic_import_runtime_observations is not None:
        analyze_kwargs["dynamic_import_runtime_observations"] = (
            dynamic_import_runtime_observations
        )
    if eval_runtime_observations is not None:
        analyze_kwargs["eval_runtime_observations"] = eval_runtime_observations
    if hasattr_runtime_observations is not None:
        analyze_kwargs["hasattr_runtime_observations"] = hasattr_runtime_observations
    if getattr_runtime_observations is not None:
        analyze_kwargs["getattr_runtime_observations"] = getattr_runtime_observations
    if vars_runtime_observations is not None:
        analyze_kwargs["vars_runtime_observations"] = vars_runtime_observations
    if globals_runtime_observations is not None:
        analyze_kwargs["globals_runtime_observations"] = globals_runtime_observations
    if locals_runtime_observations is not None:
        analyze_kwargs["locals_runtime_observations"] = locals_runtime_observations
    if metaclass_behavior_runtime_observations is not None:
        analyze_kwargs["metaclass_behavior_runtime_observations"] = (
            metaclass_behavior_runtime_observations
        )
    if setattr_runtime_observations is not None:
        analyze_kwargs["setattr_runtime_observations"] = setattr_runtime_observations
    if dir_runtime_observations is not None:
        analyze_kwargs["dir_runtime_observations"] = dir_runtime_observations

    if analyze_kwargs:
        program = analyze_repository(request.repo_root, **analyze_kwargs)
    else:
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
