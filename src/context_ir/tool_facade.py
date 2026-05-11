"""Tool-facing facade over repository analysis and semantic compilation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, TypedDict

from context_ir.analyzer import analyze_repository
from context_ir.runtime_observation_admission import (
    RuntimeObservation,
    RuntimeObservationApplication,
    RuntimeProbeResultBatchAdmission,
)
from context_ir.runtime_observation_recompile import (
    RuntimeObservationRecompileApplication,
    RuntimeProbeResultBatchRecompileApplication,
    RuntimeProbeRunnerCallableRecompileApplication,
    apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile,
    apply_runtime_observations_for_diagnostic_and_recompile,
)
from context_ir.runtime_probe_execution import (
    RuntimeProbeDiagnosticRunnerRequestPreparation,
    RuntimeProbeRunnerAttemptCollection,
)
from context_ir.runtime_probe_results import (
    RuntimeProbeNonProofResult,
    RuntimeProbeReplayField,
)
from context_ir.semantic_compiler import compile_semantic_context
from context_ir.semantic_types import (
    RepositorySnapshotBasis,
    ResolverDiagnostic,
    SemanticCompileResult,
    SemanticDiagnosticResult,
    SemanticMissEvidence,
    SemanticOptimizationWarning,
    SemanticProgram,
    SemanticRecompileResult,
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
        ExecRuntimeObservation,
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
    exec_runtime_observations: Sequence[ExecRuntimeObservation]
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
    exec_runtime_observations: Sequence[ExecRuntimeObservation] | None = None
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


@dataclass(frozen=True)
class SemanticRuntimeObservationRecompileRequest:
    """Inputs for applying typed runtime observations before recompilation."""

    previous_response: SemanticContextResponse
    diagnostic: SemanticDiagnosticResult
    runtime_observations: Sequence[RuntimeObservation]
    miss_evidence: SemanticMissEvidence
    delta_budget: int
    embed_fn: EmbeddingFunction | None = None


@dataclass(frozen=True)
class SemanticRuntimeObservationRecompileResponse:
    """Transparent facade result for runtime-observation recompilation."""

    runtime_observation_recompile: RuntimeObservationRecompileApplication
    observation_application: RuntimeObservationApplication
    recompile_result: SemanticRecompileResult
    program: SemanticProgram
    compile_result: SemanticCompileResult
    diagnostic: SemanticDiagnosticResult
    compile_total_tokens: int
    compile_budget: int
    budget_delta: int
    newly_selected_unit_ids: tuple[str, ...]
    upgraded_unit_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject facade surfaces that diverge from the underlying recompile."""
        if (
            self.observation_application
            is not self.runtime_observation_recompile.observation_application
        ):
            raise ValueError(
                "observation_application must mirror runtime_observation_recompile"
            )
        if self.recompile_result is not (
            self.runtime_observation_recompile.recompile_result
        ):
            raise ValueError(
                "recompile_result must mirror runtime_observation_recompile"
            )
        if self.program is not self.observation_application.updated_program:
            raise ValueError("program must mirror observation_application")
        if self.compile_result is not self.recompile_result.compile_result:
            raise ValueError("compile_result must mirror recompile_result")
        if self.diagnostic is not self.recompile_result.diagnostic:
            raise ValueError("diagnostic must mirror recompile_result")
        if self.compile_total_tokens != self.compile_result.total_tokens:
            raise ValueError("compile_total_tokens must mirror compile_result")
        if self.compile_budget != self.compile_result.budget:
            raise ValueError("compile_budget must mirror compile_result")
        if self.budget_delta != self.recompile_result.budget_delta:
            raise ValueError("budget_delta must mirror recompile_result")
        if (
            self.newly_selected_unit_ids
            != self.recompile_result.newly_selected_unit_ids
        ):
            raise ValueError("newly_selected_unit_ids must mirror recompile_result")
        if self.upgraded_unit_ids != self.recompile_result.upgraded_unit_ids:
            raise ValueError("upgraded_unit_ids must mirror recompile_result")


@dataclass(frozen=True)
class SemanticDynamicImportLocalPythonSubprocessRecompileRequest:
    """Inputs for subprocess-backed dynamic-import probing before recompilation."""

    previous_response: SemanticContextResponse
    diagnostic: SemanticDiagnosticResult
    miss_evidence: SemanticMissEvidence
    delta_budget: int
    python_executable: str
    invocation_contract_revision: str
    completion_contract_revision: str
    repository_snapshot_basis: RepositorySnapshotBasis
    probe_contract_revision: str
    runtime_assumptions: Sequence[RuntimeProbeReplayField]
    runner_contract_revision: str
    timeout_seconds: int
    runner_environment: Sequence[RuntimeProbeReplayField]
    runner_assumptions: Sequence[RuntimeProbeReplayField]
    embed_fn: EmbeddingFunction | None = None


@dataclass(frozen=True)
class SemanticDynamicImportLocalPythonSubprocessRecompileResponse:
    """Transparent facade result for subprocess-backed dynamic-import recompile."""

    dynamic_import_local_python_subprocess_recompile: (
        RuntimeProbeRunnerCallableRecompileApplication
    )
    runner_request_preparation: RuntimeProbeDiagnosticRunnerRequestPreparation
    runner_attempt_collection: RuntimeProbeRunnerAttemptCollection
    result_batch_recompile_application: RuntimeProbeResultBatchRecompileApplication
    result_batch_admission: RuntimeProbeResultBatchAdmission
    non_proof_results: tuple[RuntimeProbeNonProofResult, ...]
    observation_application: RuntimeObservationApplication
    recompile_result: SemanticRecompileResult
    program: SemanticProgram
    compile_result: SemanticCompileResult
    diagnostic: SemanticDiagnosticResult
    compile_total_tokens: int
    compile_budget: int
    budget_delta: int
    newly_selected_unit_ids: tuple[str, ...]
    upgraded_unit_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject facade surfaces that diverge from the nested recompile result."""
        subprocess_recompile = self.dynamic_import_local_python_subprocess_recompile
        if self.runner_request_preparation is not (
            subprocess_recompile.runner_request_preparation
        ):
            raise ValueError(
                "runner_request_preparation must mirror "
                "dynamic_import_local_python_subprocess_recompile"
            )
        if self.runner_attempt_collection is not (
            subprocess_recompile.runner_attempt_collection
        ):
            raise ValueError(
                "runner_attempt_collection must mirror "
                "dynamic_import_local_python_subprocess_recompile"
            )
        if self.result_batch_recompile_application is not (
            subprocess_recompile.result_batch_recompile_application
        ):
            raise ValueError(
                "result_batch_recompile_application must mirror "
                "dynamic_import_local_python_subprocess_recompile"
            )
        if (
            self.result_batch_admission
            is not self.result_batch_recompile_application.result_batch_admission
        ):
            raise ValueError(
                "result_batch_admission must mirror result_batch_recompile_application"
            )
        if self.non_proof_results is not (
            self.result_batch_recompile_application.non_proof_results
        ):
            raise ValueError(
                "non_proof_results must mirror result_batch_recompile_application"
            )
        if (
            self.observation_application
            is not self.result_batch_recompile_application.observation_application
        ):
            raise ValueError(
                "observation_application must mirror result_batch_recompile_application"
            )
        if (
            self.recompile_result
            is not self.result_batch_recompile_application.recompile_result
        ):
            raise ValueError(
                "recompile_result must mirror result_batch_recompile_application"
            )
        if self.program is not self.observation_application.updated_program:
            raise ValueError("program must mirror observation_application")
        if self.compile_result is not self.recompile_result.compile_result:
            raise ValueError("compile_result must mirror recompile_result")
        if self.diagnostic is not self.recompile_result.diagnostic:
            raise ValueError("diagnostic must mirror recompile_result")
        if self.compile_total_tokens != self.compile_result.total_tokens:
            raise ValueError("compile_total_tokens must mirror compile_result")
        if self.compile_budget != self.compile_result.budget:
            raise ValueError("compile_budget must mirror compile_result")
        if self.budget_delta != self.recompile_result.budget_delta:
            raise ValueError("budget_delta must mirror recompile_result")
        if (
            self.newly_selected_unit_ids
            != self.recompile_result.newly_selected_unit_ids
        ):
            raise ValueError("newly_selected_unit_ids must mirror recompile_result")
        if self.upgraded_unit_ids != self.recompile_result.upgraded_unit_ids:
            raise ValueError("upgraded_unit_ids must mirror recompile_result")


def compile_repository_context(
    request: SemanticContextRequest,
) -> SemanticContextResponse:
    """Analyze a repository and compile a semantic context response."""
    dynamic_import_runtime_observations = request.dynamic_import_runtime_observations
    eval_runtime_observations = request.eval_runtime_observations
    exec_runtime_observations = request.exec_runtime_observations
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
    if exec_runtime_observations is not None:
        analyze_kwargs["exec_runtime_observations"] = exec_runtime_observations
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


def recompile_repository_context_with_runtime_observations(
    request: SemanticRuntimeObservationRecompileRequest,
) -> SemanticRuntimeObservationRecompileResponse:
    """Apply typed runtime observations and recompile a prior facade response."""
    runtime_observation_recompile = (
        apply_runtime_observations_for_diagnostic_and_recompile(
            request.previous_response.program,
            request.diagnostic,
            request.runtime_observations,
            request.previous_response.compile_result,
            request.miss_evidence,
            request.delta_budget,
            embed_fn=request.embed_fn,
        )
    )
    observation_application = runtime_observation_recompile.observation_application
    recompile_result = runtime_observation_recompile.recompile_result
    compile_result = recompile_result.compile_result
    return SemanticRuntimeObservationRecompileResponse(
        runtime_observation_recompile=runtime_observation_recompile,
        observation_application=observation_application,
        recompile_result=recompile_result,
        program=observation_application.updated_program,
        compile_result=compile_result,
        diagnostic=recompile_result.diagnostic,
        compile_total_tokens=compile_result.total_tokens,
        compile_budget=compile_result.budget,
        budget_delta=recompile_result.budget_delta,
        newly_selected_unit_ids=recompile_result.newly_selected_unit_ids,
        upgraded_unit_ids=recompile_result.upgraded_unit_ids,
    )


def recompile_repository_context_with_dynamic_import_local_python_subprocess(
    request: SemanticDynamicImportLocalPythonSubprocessRecompileRequest,
) -> SemanticDynamicImportLocalPythonSubprocessRecompileResponse:
    """Run local-Python dynamic-import probes and recompile a prior response."""
    dynamic_import_local_python_subprocess_recompile = (
        apply_dynamic_import_local_python_subprocess_for_diagnostic_and_recompile(
            request.previous_response.program,
            request.diagnostic,
            request.previous_response.compile_result,
            request.miss_evidence,
            request.delta_budget,
            python_executable=request.python_executable,
            invocation_contract_revision=request.invocation_contract_revision,
            completion_contract_revision=request.completion_contract_revision,
            repository_snapshot_basis=request.repository_snapshot_basis,
            probe_contract_revision=request.probe_contract_revision,
            runtime_assumptions=request.runtime_assumptions,
            runner_contract_revision=request.runner_contract_revision,
            timeout_seconds=request.timeout_seconds,
            runner_environment=request.runner_environment,
            runner_assumptions=request.runner_assumptions,
            embed_fn=request.embed_fn,
        )
    )
    subprocess_recompile = dynamic_import_local_python_subprocess_recompile
    result_batch_recompile_application = (
        subprocess_recompile.result_batch_recompile_application
    )
    observation_application = result_batch_recompile_application.observation_application
    recompile_result = result_batch_recompile_application.recompile_result
    compile_result = recompile_result.compile_result
    return SemanticDynamicImportLocalPythonSubprocessRecompileResponse(
        dynamic_import_local_python_subprocess_recompile=(
            dynamic_import_local_python_subprocess_recompile
        ),
        runner_request_preparation=(
            dynamic_import_local_python_subprocess_recompile.runner_request_preparation
        ),
        runner_attempt_collection=(
            dynamic_import_local_python_subprocess_recompile.runner_attempt_collection
        ),
        result_batch_recompile_application=result_batch_recompile_application,
        result_batch_admission=(
            result_batch_recompile_application.result_batch_admission
        ),
        non_proof_results=result_batch_recompile_application.non_proof_results,
        observation_application=observation_application,
        recompile_result=recompile_result,
        program=observation_application.updated_program,
        compile_result=compile_result,
        diagnostic=recompile_result.diagnostic,
        compile_total_tokens=compile_result.total_tokens,
        compile_budget=compile_result.budget,
        budget_delta=recompile_result.budget_delta,
        newly_selected_unit_ids=recompile_result.newly_selected_unit_ids,
        upgraded_unit_ids=recompile_result.upgraded_unit_ids,
    )


__all__ = [
    "EmbeddingFunction",
    "SemanticContextRequest",
    "SemanticContextResponse",
    "SemanticDynamicImportLocalPythonSubprocessRecompileRequest",
    "SemanticDynamicImportLocalPythonSubprocessRecompileResponse",
    "SemanticRuntimeObservationRecompileRequest",
    "SemanticRuntimeObservationRecompileResponse",
    "compile_repository_context",
    "recompile_repository_context_with_dynamic_import_local_python_subprocess",
    "recompile_repository_context_with_runtime_observations",
]
