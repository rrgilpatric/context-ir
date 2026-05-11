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
from context_ir.runtime_probe_execution import (
    RuntimeProbeDiagnosticRunnerRequestPreparation,
    RuntimeProbeRunnerAttemptCollection,
    RuntimeProbeRunnerCallable,
    collect_runtime_probe_execution_attempts_from_runner_requests,
    make_runtime_probe_dynamic_import_local_python_subprocess_runner,
    prepare_runtime_probe_runner_requests_for_diagnostic,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeNonProofResult,
    RuntimeProbeReplayField,
    RuntimeProbeResultBatch,
)
from context_ir.semantic_diagnostics import recompile_semantic_context
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
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


@dataclass(frozen=True)
class RuntimeProbeRunnerCallableRecompileApplication:
    """Result of runner-callable probe execution before semantic recompile."""

    runner_request_preparation: RuntimeProbeDiagnosticRunnerRequestPreparation
    runner_attempt_collection: RuntimeProbeRunnerAttemptCollection
    result_batch_recompile_application: RuntimeProbeResultBatchRecompileApplication


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


def apply_runtime_probe_runner_for_diagnostic_and_recompile(
    program: SemanticProgram,
    diagnostic: SemanticDiagnosticResult,
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    delta_budget: int,
    *,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: Iterable[RuntimeProbeReplayField],
    runner_contract_revision: str,
    timeout_seconds: int,
    runner_environment: Iterable[RuntimeProbeReplayField],
    runner_assumptions: Iterable[RuntimeProbeReplayField],
    runner: RuntimeProbeRunnerCallable,
    embed_fn: EmbeddingFunction | None = None,
) -> RuntimeProbeRunnerCallableRecompileApplication:
    """Prepare runner requests, collect attempts, admit results, then recompile."""
    runner_request_preparation = prepare_runtime_probe_runner_requests_for_diagnostic(
        diagnostic,
        repository_snapshot_basis=repository_snapshot_basis,
        probe_contract_revision=probe_contract_revision,
        runtime_assumptions=runtime_assumptions,
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=runner_environment,
        runner_assumptions=runner_assumptions,
    )
    runner_attempt_collection = (
        collect_runtime_probe_execution_attempts_from_runner_requests(
            runner_request_preparation.runner_request_batch,
            runner,
        )
    )
    result_batch_recompile_application = (
        apply_runtime_probe_result_batch_for_diagnostic_and_recompile(
            program,
            diagnostic,
            runner_attempt_collection.result_batch,
            previous_result,
            miss_evidence,
            delta_budget,
            embed_fn=embed_fn,
        )
    )
    return RuntimeProbeRunnerCallableRecompileApplication(
        runner_request_preparation=runner_request_preparation,
        runner_attempt_collection=runner_attempt_collection,
        result_batch_recompile_application=result_batch_recompile_application,
    )


def apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile(
    program: SemanticProgram,
    diagnostic: SemanticDiagnosticResult,
    previous_result: SemanticCompileResult,
    miss_evidence: SemanticMissEvidence,
    delta_budget: int,
    *,
    python_executable: str,
    invocation_contract_revision: str,
    completion_contract_revision: str,
    repository_snapshot_basis: RepositorySnapshotBasis,
    probe_contract_revision: str,
    runtime_assumptions: Iterable[RuntimeProbeReplayField],
    runner_contract_revision: str,
    timeout_seconds: int,
    runner_environment: Iterable[RuntimeProbeReplayField],
    runner_assumptions: Iterable[RuntimeProbeReplayField],
    embed_fn: EmbeddingFunction | None = None,
) -> RuntimeProbeRunnerCallableRecompileApplication:
    """Apply the default dynamic-import local-Python runner, then recompile."""
    runner = make_runtime_probe_dynamic_import_local_python_subprocess_runner(
        python_executable=python_executable,
        invocation_contract_revision=invocation_contract_revision,
        completion_contract_revision=completion_contract_revision,
    )
    return apply_runtime_probe_runner_for_diagnostic_and_recompile(
        program,
        diagnostic,
        previous_result,
        miss_evidence,
        delta_budget,
        repository_snapshot_basis=repository_snapshot_basis,
        probe_contract_revision=probe_contract_revision,
        runtime_assumptions=runtime_assumptions,
        runner_contract_revision=runner_contract_revision,
        timeout_seconds=timeout_seconds,
        runner_environment=runner_environment,
        runner_assumptions=runner_assumptions,
        runner=runner,
        embed_fn=embed_fn,
    )


__all__ = [
    "RuntimeObservationRecompileApplication",
    "apply_runtime_observations_for_diagnostic_and_recompile",
]
