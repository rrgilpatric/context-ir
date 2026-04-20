"""Public semantic repository analysis orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_acquisition import (
    DynamicImportRuntimeObservation,
    GetattrRuntimeObservation,
    HasattrRuntimeObservation,
    VarsRuntimeObservation,
    attach_dynamic_import_runtime_provenance,
    attach_getattr_runtime_provenance,
    attach_hasattr_runtime_provenance,
    attach_vars_runtime_provenance,
)
from context_ir.semantic_types import SemanticProgram


def analyze_repository(
    repo_root: Path | str,
    *,
    dynamic_import_runtime_observations: Sequence[DynamicImportRuntimeObservation] = (),
    hasattr_runtime_observations: Sequence[HasattrRuntimeObservation] = (),
    getattr_runtime_observations: Sequence[GetattrRuntimeObservation] = (),
    vars_runtime_observations: Sequence[VarsRuntimeObservation] = (),
) -> SemanticProgram:
    """Analyze ``repo_root`` into the fully derived semantic program."""
    syntax = extract_syntax(repo_root)
    bound_program = bind_syntax(syntax)
    resolved_program = resolve_semantics(bound_program)
    derived_program = derive_dependency_frontier(resolved_program)
    if (
        not dynamic_import_runtime_observations
        and not hasattr_runtime_observations
        and not getattr_runtime_observations
        and not vars_runtime_observations
    ):
        return derived_program

    program = derived_program
    if dynamic_import_runtime_observations:
        program = attach_dynamic_import_runtime_provenance(
            program,
            dynamic_import_runtime_observations,
        )
    if hasattr_runtime_observations:
        program = attach_hasattr_runtime_provenance(
            program,
            hasattr_runtime_observations,
        )
    if getattr_runtime_observations:
        program = attach_getattr_runtime_provenance(
            program,
            getattr_runtime_observations,
        )
    if vars_runtime_observations:
        program = attach_vars_runtime_provenance(
            program,
            vars_runtime_observations,
        )
    return program


__all__ = ["analyze_repository"]
