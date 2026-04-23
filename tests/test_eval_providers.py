"""Deterministic eval provider and baseline infrastructure tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import context_ir
import context_ir.eval_providers as eval_providers
import context_ir.semantic_types as semantic_types
from context_ir.semantic_types import (
    CapabilityTier,
    EvidenceOriginKind,
    ReplayStatus,
    SelectionBasis,
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticSelectionRecord,
    SemanticSubjectKind,
    SemanticUnitTraceSummary,
    SyntaxProgram,
)
from context_ir.tool_facade import SemanticContextRequest, SemanticContextResponse

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_FIXTURE_ROOT = (
    REPO_ROOT / "evals" / "fixtures" / "oracle_signal_dynamic_import_probe"
)
HASATTR_PROBE_FIXTURE_ROOT = (
    REPO_ROOT / "evals" / "fixtures" / "oracle_signal_hasattr_probe"
)
PROBE_QUERY = (
    'Fix unsupported dynamic import import_module("plugins.weather") '
    "while keeping probe digest output aligned"
)
HASATTR_PROBE_QUERY = (
    "Fix probe_attribute unsupported hasattr(obj, name) and keep digest output aligned"
)


def _write_file(repo_root: Path, relative_path: str, text: str) -> None:
    """Write one UTF-8 fixture file below ``repo_root``."""
    path = repo_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _request(
    repo_root: Path,
    *,
    query: str,
    budget: int = 1000,
) -> eval_providers.EvalProviderRequest:
    """Build a standard provider request for tests."""
    return eval_providers.EvalProviderRequest(
        repo_root=repo_root,
        task_id="task",
        query=query,
        budget=budget,
    )


def test_shared_token_estimator_matches_eval_formula() -> None:
    """The shared estimator uses the accepted ceil-by-four heuristic."""
    assert eval_providers.estimate_tokens("") == 1
    assert eval_providers.estimate_tokens("a") == 1
    assert eval_providers.estimate_tokens("abcd") == 1
    assert eval_providers.estimate_tokens("abcde") == 2
    text = "x" * 17
    assert eval_providers.estimate_tokens(text) == max(1, (len(text) + 3) // 4)


def test_lexical_tokenization_handles_punctuation_paths_and_camel_case(
    tmp_path: Path,
) -> None:
    """Lexical terms are deterministic across punctuation, paths, and casing."""
    assert eval_providers.lexical_tokens("CallHTTPServer pkg/myFile.py") == (
        "callhttpserver",
        "call",
        "http",
        "server",
        "pkg",
        "pkg",
        "myfile",
        "my",
        "file",
        "py",
        "py",
    )
    _write_file(tmp_path, "pkg/myFile.py", "def unrelated() -> None:\n    pass\n")

    result = eval_providers.build_lexical_top_k_files_pack(
        _request(tmp_path, query="my file", budget=200)
    )

    assert result.selected_files == ("pkg/myFile.py",)
    assert "## pkg/myFile.py" in result.document


def test_lexical_baseline_orders_by_score_token_count_and_path(
    tmp_path: Path,
) -> None:
    """Lexical candidates are sorted by score, file token count, then path."""
    _write_file(tmp_path, "high.py", "alpha beta\n")
    _write_file(tmp_path, "a.py", "alpha\n")
    _write_file(tmp_path, "b.py", "alpha\n")
    _write_file(tmp_path, "long.py", "alpha\n" + ("padding " * 40))

    result = eval_providers.build_lexical_top_k_files_pack(
        _request(tmp_path, query="alpha beta", budget=1000)
    )

    assert result.selected_files == ("high.py", "a.py", "b.py", "long.py")
    assert [score.file_path for score in result.metadata.lexical_scores[:4]] == [
        "high.py",
        "a.py",
        "b.py",
        "long.py",
    ]


def test_lexical_baseline_emits_no_positive_score_with_zero_files(
    tmp_path: Path,
) -> None:
    """Lexical baseline does not fall back when no positive lexical score exists."""
    _write_file(tmp_path, "main.py", "def run() -> None:\n    pass\n")

    result = eval_providers.build_lexical_top_k_files_pack(
        _request(tmp_path, query="absent", budget=200)
    )

    assert result.selected_files == ()
    assert result.omitted_candidate_files == ()
    assert result.warnings == ("no_positive_lexical_score",)
    assert "selected_files: 0" in result.document
    assert "warnings: 1" in result.document


def test_baseline_packing_counts_headers_and_skips_oversized_files(
    tmp_path: Path,
) -> None:
    """Whole-file packing accounts for headers and skips files without truncation."""
    _write_file(tmp_path, "big.py", "target unique\n" + ("X" * 1000))
    _write_file(tmp_path, "small.py", "target\n")

    result = eval_providers.build_lexical_top_k_files_pack(
        _request(tmp_path, query="target unique", budget=80)
    )

    assert result.total_tokens <= result.budget
    assert result.selected_files == ("small.py",)
    assert result.omitted_candidate_files == ("big.py",)
    assert "## small.py\ntarget\n" in result.document
    assert "## big.py" not in result.document
    assert "X" * 100 not in result.document


def test_import_neighborhood_selects_seeds_direct_imports_not_transitive(
    tmp_path: Path,
) -> None:
    """Import-neighborhood uses lexical seeds and one direct import hop only."""
    _write_file(
        tmp_path,
        "main.py",
        textwrap.dedent(
            """
            from pkg.helpers import helper

            def target() -> None:
                helper()
            """
        ).lstrip(),
    )
    _write_file(
        tmp_path,
        "pkg/helpers.py",
        textwrap.dedent(
            """
            from pkg.deep import deep

            def helper() -> None:
                deep()
            """
        ).lstrip(),
    )
    _write_file(tmp_path, "pkg/deep.py", "def deep() -> None:\n    pass\n")

    result = eval_providers.build_import_neighborhood_files_pack(
        _request(tmp_path, query="target", budget=1000)
    )

    assert result.selected_files == ("main.py", "pkg/helpers.py")
    assert "## pkg/deep.py" not in result.document


def test_import_neighborhood_handles_star_import_warning(tmp_path: Path) -> None:
    """Star imports include the module but record that symbols were not expanded."""
    _write_file(
        tmp_path,
        "main.py",
        "from pkg.helpers import *\n\ndef target() -> None:\n    helper()\n",
    )
    _write_file(tmp_path, "pkg/helpers.py", "def helper() -> None:\n    pass\n")

    result = eval_providers.build_import_neighborhood_files_pack(
        _request(tmp_path, query="target", budget=1000)
    )

    assert result.selected_files == ("main.py", "pkg/helpers.py")
    assert "star_import_not_expanded" in result.warnings
    assert "warnings: 1" in result.document


def test_import_neighborhood_handles_missing_external_imports(tmp_path: Path) -> None:
    """Missing and external imports warn without adding non-repo files."""
    _write_file(
        tmp_path,
        "main.py",
        (
            "import os\n"
            "from missing.module import thing\n\n"
            "def target() -> None:\n"
            "    pass\n"
        ),
    )

    result = eval_providers.build_import_neighborhood_files_pack(
        _request(tmp_path, query="target", budget=1000)
    )

    assert result.selected_files == ("main.py",)
    assert result.metadata.candidate_files == ("main.py",)
    assert result.warnings == ("import_not_resolved",)
    assert "## os.py" not in result.document
    assert "## missing/module.py" not in result.document


def test_file_order_floor_is_diagnostic_only(tmp_path: Path) -> None:
    """The file-order baseline is marked as diagnostic-only metadata."""
    _write_file(tmp_path, "b.py", "VALUE = 'b'\n")
    _write_file(tmp_path, "a.py", "VALUE = 'a'\n")

    result = eval_providers.build_file_order_floor_pack(
        _request(tmp_path, query="", budget=1000)
    )

    assert result.provider_name == eval_providers.FILE_ORDER_FLOOR_PROVIDER
    assert result.provider_config.diagnostic_only is True
    assert result.metadata.diagnostic_only is True
    assert result.selected_files == ("a.py", "b.py")


def test_context_ir_provider_delegates_to_facade_with_no_embed_fn(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Context IR provider calls compile_repository_context with embed_fn=None."""
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    selection = SemanticSelectionRecord(
        unit_id="unit:selected",
        detail="identity",
        token_count=1,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="fake trace",
        edit_score=0.1,
        support_score=0.0,
        trace_summary=SemanticUnitTraceSummary(
            subject_id="unit:selected",
            subject_kind=SemanticSubjectKind.SYMBOL,
            primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
            attached_runtime_provenance_record_ids=("prov:symbol:runtime:1",),
        ),
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
        message="fake warning",
        unit_id="unit:selected",
    )
    optimization = SemanticOptimizationResult(
        selections=(selection,),
        omitted_unit_ids=("unit:omitted",),
        warnings=(warning,),
        total_tokens=1,
        budget=100,
        confidence=0.5,
    )
    document = "# Semantic Context\nfake"
    compile_result = SemanticCompileResult(
        document=document,
        optimization=optimization,
        omitted_unit_ids=("unit:omitted",),
        total_tokens=eval_providers.estimate_tokens(document),
        budget=100,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="target"),
    )
    response = SemanticContextResponse(
        program=program,
        compile_result=compile_result,
        unresolved_frontier=(),
        unsupported_constructs=(),
        syntax_diagnostics=(),
        semantic_diagnostics=(),
        optimization_warnings=(warning,),
        selection_trace=(selection,),
        omitted_unit_ids=("unit:omitted",),
        compile_total_tokens=eval_providers.estimate_tokens(document),
        compile_budget=100,
    )
    calls: list[SemanticContextRequest] = []

    def fake_compile(request: SemanticContextRequest) -> SemanticContextResponse:
        calls.append(request)
        return response

    monkeypatch.setattr(
        eval_providers.tool_facade,
        "compile_repository_context",
        fake_compile,
    )

    result = eval_providers.build_context_ir_provider_pack(
        _request(tmp_path, query="target", budget=100)
    )

    assert len(calls) == 1
    assert calls[0].repo_root == tmp_path
    assert calls[0].query == "target"
    assert calls[0].budget == 100
    assert calls[0].embed_fn is None
    assert result.document == document
    assert result.selected_unit_ids == ("unit:selected",)
    assert result.omitted_unit_ids == ("unit:omitted",)
    assert result.warnings == ("budget_pressure",)
    assert result.metadata.selected_units == (
        eval_providers.EvalSelectedUnit(
            unit_id="unit:selected",
            detail="identity",
            token_count=1,
            basis="heuristic_candidate",
            reason="fake trace",
            edit_score=0.1,
            support_score=0.0,
            primary_capability_tier=CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=EvidenceOriginKind.STATIC_DERIVATION_RULE,
            primary_replay_status=ReplayStatus.DETERMINISTIC_STATIC,
            has_attached_runtime_provenance=True,
            attached_runtime_provenance_record_ids=("prov:symbol:runtime:1",),
        ),
    )
    assert result.metadata.warning_details == (
        eval_providers.EvalProviderWarning(
            code="budget_pressure",
            unit_id="unit:selected",
            message="fake warning",
        ),
    )
    assert tuple(unit.unit_id for unit in result.metadata.selected_units) == (
        result.selected_unit_ids
    )
    assert (
        tuple(
            provider_warning.code
            for provider_warning in result.metadata.warning_details
        )
        == result.warnings
    )


def test_context_ir_provider_attaches_dynamic_import_runtime_probe_metadata() -> None:
    """Context IR provider exposes additive runtime provenance from fixture probes."""
    result = eval_providers.build_context_ir_provider_pack(
        eval_providers.EvalProviderRequest(
            repo_root=PROBE_FIXTURE_ROOT,
            task_id="oracle_signal_dynamic_import_probe",
            query=PROBE_QUERY,
            budget=220,
        )
    )
    unsupported = next(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id == "unsupported:call:main.py:5:13"
    )

    assert "unsupported:call:main.py:5:13" in result.selected_unit_ids
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_context_ir_provider_attaches_hasattr_runtime_probe_metadata() -> None:
    """Context IR provider exposes additive ``hasattr`` runtime provenance."""
    result = eval_providers.build_context_ir_provider_pack(
        eval_providers.EvalProviderRequest(
            repo_root=HASATTR_PROBE_FIXTURE_ROOT,
            task_id="oracle_signal_hasattr_probe",
            query=HASATTR_PROBE_QUERY,
            budget=220,
        )
    )
    unsupported = next(
        unit
        for unit in result.metadata.selected_units
        if unit.unit_id == "unsupported:call:main.py:2:11"
    )

    assert "unsupported:call:main.py:2:11" in result.selected_unit_ids
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_provider_outputs_carry_metadata_for_later_scoring(tmp_path: Path) -> None:
    """Baseline provider outputs expose selected, omitted, warning, and score data."""
    _write_file(tmp_path, "big.py", "target unique\n" + ("X" * 1000))
    _write_file(tmp_path, "small.py", "target\n")

    result = eval_providers.build_lexical_top_k_files_pack(
        _request(tmp_path, query="target unique", budget=80)
    )

    assert result.selected_files == ("small.py",)
    assert result.omitted_candidate_files == ("big.py",)
    assert result.metadata.candidate_files == ("big.py", "small.py")
    assert result.metadata.omitted_candidate_files == ("big.py",)
    assert {score.file_path for score in result.metadata.lexical_scores} == {
        "big.py",
        "small.py",
    }
    assert result.metadata.selected_units == ()
    assert result.metadata.warning_details == ()


def test_context_ir_results_reject_lossy_trace_or_warning_metadata() -> None:
    """Context IR results reject convenience fields that diverge from metadata."""
    document = "# Semantic Context\ntrace"
    metadata = eval_providers.EvalProviderMetadata(
        selected_units=(
            eval_providers.EvalSelectedUnit(
                unit_id="unit:selected",
                detail="summary",
                token_count=3,
                basis="proven_dependency",
            ),
        ),
        warning_details=(
            eval_providers.EvalProviderWarning(
                code="omitted_uncertainty",
                unit_id="unit:omitted",
                message="uncertainty omitted",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="selected_unit_ids must mirror structured selected-unit metadata",
    ):
        eval_providers.EvalProviderResult(
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            provider_algorithm_version=eval_providers.PROVIDER_ALGORITHM_VERSION,
            provider_config=eval_providers.EvalProviderConfig(),
            task_id="task",
            query="target",
            budget=100,
            document=document,
            total_tokens=eval_providers.estimate_tokens(document),
            selected_files=(),
            omitted_candidate_files=(),
            selected_unit_ids=("unit:other",),
            omitted_unit_ids=(),
            warnings=("omitted_uncertainty",),
            metadata=metadata,
        )

    with pytest.raises(
        ValueError,
        match="warnings must mirror structured warning metadata",
    ):
        eval_providers.EvalProviderResult(
            provider_name=eval_providers.CONTEXT_IR_PROVIDER,
            provider_algorithm_version=eval_providers.PROVIDER_ALGORITHM_VERSION,
            provider_config=eval_providers.EvalProviderConfig(),
            task_id="task",
            query="target",
            budget=100,
            document=document,
            total_tokens=eval_providers.estimate_tokens(document),
            selected_files=(),
            omitted_candidate_files=(),
            selected_unit_ids=("unit:selected",),
            omitted_unit_ids=(),
            warnings=("budget_pressure",),
            metadata=metadata,
        )


def test_baselines_do_not_accept_oracle_units_as_inputs() -> None:
    """File baselines depend only on repo source files and task query inputs."""
    request_fields = set(eval_providers.EvalProviderRequest.__dataclass_fields__)

    assert request_fields == {"repo_root", "task_id", "query", "budget"}
    assert "expected_selectors" not in request_fields
    assert "resolved_selectors" not in request_fields


def test_eval_providers_stay_internal_and_do_not_add_metric_surfaces() -> None:
    """Provider infrastructure avoids public exports and metric/report fields."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalProviderResult" not in context_ir.__all__
    assert not hasattr(context_ir, "build_lexical_top_k_files_pack")

    result_fields = set(eval_providers.EvalProviderResult.__dataclass_fields__)
    forbidden_metric_fields = {
        "aggregate_score",
        "edit_coverage",
        "support_coverage",
        "uncertainty_coverage",
        "credited_tokens",
        "noise_tokens",
        "raw_jsonl_path",
        "markdown_report",
    }

    assert forbidden_metric_fields.isdisjoint(result_fields)
