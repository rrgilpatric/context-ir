"""Compose diagnostic-gated runtime observation application with recompile."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from context_ir.runtime_observation_admission import (
    RuntimeObservation,
    RuntimeObservationApplication,
    apply_runtime_observations_for_diagnostic,
)
from context_ir.semantic_diagnostics import recompile_semantic_context
from context_ir.semantic_types import (
    SemanticCompileResult,
    SemanticDiagnosticResult,
    SemanticMissEvidence,
    SemanticProgram,
    SemanticRecompileResult,
)

EmbeddingFunction = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True)
class RuntimeObservationRecompileApplication:
    """Result of applying runtime observations before semantic recompilation."""

    observation_application: RuntimeObservationApplication
    recompile_result: SemanticRecompileResult


def apply_runtime_observations_for_diagnostic_and_recompile(
    program: SemanticProgram,
    diagnostic: SemanticDiagnosticResult,
    observations: Iterable[RuntimeObservation],
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    delta_budget: int,
    *,
    embed_fn: EmbeddingFunction | None = None,
) -> RuntimeObservationRecompileApplication:
    """Apply diagnostic-gated runtime observations, then recompile updated context."""
    observation_application = apply_runtime_observations_for_diagnostic(
        program,
        diagnostic,
        observations,
    )
    recompile_result = recompile_semantic_context(
        previous_result,
        miss_evidence,
        delta_budget,
        observation_application.updated_program,
        embed_fn=embed_fn,
    )
    return RuntimeObservationRecompileApplication(
        observation_application=observation_application,
        recompile_result=recompile_result,
    )


__all__ = [
    "RuntimeObservationRecompileApplication",
    "apply_runtime_observations_for_diagnostic_and_recompile",
]
