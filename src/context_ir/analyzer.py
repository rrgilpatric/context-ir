"""Public semantic repository analysis orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from context_ir.binder import bind_syntax
from context_ir.dependency_frontier import derive_dependency_frontier
from context_ir.parser import extract_syntax
from context_ir.resolver import resolve_semantics
from context_ir.runtime_acquisition import (
    DelattrRuntimeObservation,
    DirRuntimeObservation,
    DynamicImportRuntimeObservation,
    GetattrRuntimeObservation,
    GlobalsRuntimeObservation,
    HasattrRuntimeObservation,
    LocalsRuntimeObservation,
    MetaclassBehaviorRuntimeObservation,
    SetattrRuntimeObservation,
    VarsRuntimeObservation,
    attach_delattr_runtime_provenance,
    attach_dir_runtime_provenance,
    attach_dynamic_import_runtime_provenance,
    attach_getattr_runtime_provenance,
    attach_globals_runtime_provenance,
    attach_hasattr_runtime_provenance,
    attach_locals_runtime_provenance,
    attach_metaclass_behavior_runtime_provenance,
    attach_setattr_runtime_provenance,
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
    globals_runtime_observations: Sequence[GlobalsRuntimeObservation] = (),
    locals_runtime_observations: Sequence[LocalsRuntimeObservation] = (),
    setattr_runtime_observations: Sequence[SetattrRuntimeObservation] = (),
    delattr_runtime_observations: Sequence[DelattrRuntimeObservation] = (),
    dir_runtime_observations: Sequence[DirRuntimeObservation] = (),
    metaclass_behavior_runtime_observations: (
        Sequence[MetaclassBehaviorRuntimeObservation]
    ) = (),
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
        and not globals_runtime_observations
        and not locals_runtime_observations
        and not setattr_runtime_observations
        and not delattr_runtime_observations
        and not dir_runtime_observations
        and not metaclass_behavior_runtime_observations
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
    if globals_runtime_observations:
        program = attach_globals_runtime_provenance(
            program,
            globals_runtime_observations,
        )
    if locals_runtime_observations:
        program = attach_locals_runtime_provenance(
            program,
            locals_runtime_observations,
        )
    if setattr_runtime_observations:
        program = attach_setattr_runtime_provenance(
            program,
            setattr_runtime_observations,
        )
    if delattr_runtime_observations:
        program = attach_delattr_runtime_provenance(
            program,
            delattr_runtime_observations,
        )
    if dir_runtime_observations:
        program = attach_dir_runtime_provenance(
            program,
            dir_runtime_observations,
        )
    if metaclass_behavior_runtime_observations:
        program = attach_metaclass_behavior_runtime_provenance(
            program,
            metaclass_behavior_runtime_observations,
        )
    return program


__all__ = ["analyze_repository"]
