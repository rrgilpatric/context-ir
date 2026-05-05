"""Compose diagnostic-gated runtime observation application with recompile."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from context_ir.runtime_observation_admission import (
    RuntimeObservation,
    RuntimeObservationApplication,
    RuntimeProbeResultBatchAdmission,
    admit_runtime_probe_result_batch_for_plan,
    apply_runtime_observations_for_diagnostic,
    attach_admitted_runtime_observations,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeNonProofResult,
    RuntimeProbeResultBatch,
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


@dataclass(frozen=True)
class RuntimeProbeResultBatchRecompileApplication:
    """Result of applying runtime probe result batch admission before recompile."""

    result_batch_admission: RuntimeProbeResultBatchAdmission
    non_proof_results: tuple[RuntimeProbeNonProofResult, ...]
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


def apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
    program: SemanticProgram,
    diagnostic: SemanticDiagnosticResult,
    result_batch: RuntimeProbeResultBatch,
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    delta_budget: int,
    *,
    embed_fn: EmbeddingFunction | None = None,
) -> RuntimeProbeResultBatchRecompileApplication:
    """Admit observed probe results, preserve failures, then recompile context."""
    plan = diagnostic.planned_runtime_probe_request_plan
    if plan is None:
        raise ValueError(
            "planned_runtime_probe_request_plan is required for runtime probe "
            "result batch admission"
        )

    result_batch_admission = admit_runtime_probe_result_batch_for_plan(
        plan,
        result_batch,
    )
    updated_program = attach_admitted_runtime_observations(
        program,
        result_batch_admission.admissions,
    )
    observation_application = RuntimeObservationApplication(
        diagnostic=diagnostic,
        admissions=result_batch_admission.admissions,
        updated_program=updated_program,
    )
    recompile_result = recompile_semantic_context(
        previous_result,
        miss_evidence,
        delta_budget,
        updated_program,
        embed_fn=embed_fn,
    )
    return RuntimeProbeResultBatchRecompileApplication(
        result_batch_admission=result_batch_admission,
        non_proof_results=result_batch_admission.non_proof_results,
        observation_application=observation_application,
        recompile_result=recompile_result,
    )


__all__ = [
    "RuntimeObservationRecompileApplication",
    "apply_runtime_observations_for_diagnostic_and_recompile",
]
