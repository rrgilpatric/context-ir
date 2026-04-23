"""Deterministic raw eval result record tests."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import context_ir
import context_ir.eval_results as eval_results
import context_ir.semantic_types as semantic_types
from context_ir.eval_metrics import score_eval_run
from context_ir.eval_oracles import (
    EvalOracleSetup,
    ResolvedOracleSelector,
    setup_eval_oracle_task,
)
from context_ir.eval_providers import (
    CONTEXT_IR_PROVIDER,
    PROVIDER_ALGORITHM_VERSION,
    EvalProviderConfig,
    EvalProviderMetadata,
    EvalProviderResult,
    EvalProviderWarning,
    EvalSelectedUnit,
    estimate_tokens,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json"


def _document_for_total_tokens(total_tokens: int) -> str:
    """Return non-empty text whose estimated tokens equal ``total_tokens``."""
    if total_tokens <= 0:
        raise ValueError("total_tokens must be > 0")
    return "x" * (total_tokens * 4)


def _resolved_unit_id(resolved_selector: ResolvedOracleSelector) -> str:
    """Return the concrete unit identifier for one resolved selector."""
    unit_id = resolved_selector.resolved_unit_id
    if unit_id is None:
        raise AssertionError("resolved selector is missing resolved_unit_id")
    return unit_id


def _smoke_setup() -> EvalOracleSetup:
    """Return the accepted smoke oracle setup."""
    return setup_eval_oracle_task(TASK_PATH)


def _smoke_provider_result(setup: EvalOracleSetup) -> EvalProviderResult:
    """Return one deterministic provider result for the smoke oracle fixture."""
    edit_selector, support_selector, frontier_selector, unsupported_selector = (
        setup.resolved_selectors
    )
    frontier_unit_id = _resolved_unit_id(frontier_selector)
    unsupported_unit_id = _resolved_unit_id(unsupported_selector)
    selected_units = (
        EvalSelectedUnit(
            unit_id=_resolved_unit_id(edit_selector),
            detail="source",
            token_count=12,
            basis="pinned_obligation",
            reason="Primary edit target kept at source detail.",
            edit_score=1.0,
            support_score=0.2,
            primary_capability_tier=semantic_types.CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=(
                semantic_types.EvidenceOriginKind.STATIC_DERIVATION_RULE
            ),
            primary_replay_status=semantic_types.ReplayStatus.DETERMINISTIC_STATIC,
            has_attached_runtime_provenance=False,
        ),
        EvalSelectedUnit(
            unit_id=_resolved_unit_id(support_selector),
            detail="summary",
            token_count=6,
            basis="proven_dependency",
            reason="Direct support dependency for the edit target.",
            edit_score=0.3,
            support_score=0.9,
            primary_capability_tier=semantic_types.CapabilityTier.STATICALLY_PROVED,
            primary_evidence_origin=(
                semantic_types.EvidenceOriginKind.STATIC_DERIVATION_RULE
            ),
            primary_replay_status=semantic_types.ReplayStatus.DETERMINISTIC_STATIC,
            has_attached_runtime_provenance=False,
        ),
    )
    warning_details = (
        EvalProviderWarning(
            code="omitted_uncertainty",
            unit_id=frontier_unit_id,
            message="Frontier uncertainty omitted under budget pressure.",
        ),
        EvalProviderWarning(
            code="omitted_uncertainty",
            unit_id=unsupported_unit_id,
            message="Unsupported construct omitted under budget pressure.",
        ),
    )
    document = _document_for_total_tokens(64)
    metadata = EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
        unresolved_unit_ids=(frontier_unit_id,),
        unsupported_unit_ids=(unsupported_unit_id,),
    )
    return EvalProviderResult(
        provider_name=CONTEXT_IR_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(),
        task_id=setup.task.task_id,
        query="Fix missing_call in run without breaking helper usage",
        budget=96,
        document=document,
        total_tokens=estimate_tokens(document),
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=tuple(unit.unit_id for unit in selected_units),
        omitted_unit_ids=(frontier_unit_id, unsupported_unit_id),
        warnings=tuple(warning.code for warning in warning_details),
        metadata=metadata,
    )


def _build_smoke_inputs() -> tuple[EvalOracleSetup, EvalProviderResult, object]:
    """Return one accepted smoke setup/provider/metric triple."""
    setup = _smoke_setup()
    result = _smoke_provider_result(setup)
    metrics = score_eval_run(setup, result)
    return setup, result, metrics


def _expected_fixture_hashes(repo_root: Path) -> dict[str, str]:
    """Return the expected deterministic fixture hashes for one repo root."""
    hashes: dict[str, str] = {}
    for file_path in sorted(repo_root.rglob("*.py")):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(repo_root).as_posix()
        hashes[relative_path] = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return hashes


def test_build_eval_run_record_is_deterministic_and_json_safe() -> None:
    """One accepted triple becomes one deterministic JSON-safe raw record."""
    setup, result, metrics = _build_smoke_inputs()

    first_record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-001",
        git_commit="abc1234",
        python_version=sys.version.split()[0],
        package_version=context_ir.__version__,
    )
    second_record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-001",
        git_commit="abc1234",
        python_version=sys.version.split()[0],
        package_version=context_ir.__version__,
    )

    assert first_record == second_record

    payload = eval_results.eval_run_record_to_json(first_record)

    assert payload["spec_version"] == "v1"
    assert payload["run_id"] == "run-001"
    assert payload["task_id"] == "oracle_smoke"
    assert payload["fixture_id"] == "oracle_smoke"
    assert payload["provider_name"] == CONTEXT_IR_PROVIDER
    assert payload["provider_algorithm_version"] == PROVIDER_ALGORITHM_VERSION
    assert payload["package_version"] == context_ir.__version__
    assert payload["budget"] == result.budget
    assert payload["total_tokens"] == result.total_tokens
    assert payload["selected_unit_ids"] == list(result.selected_unit_ids)
    assert payload["omitted_unit_ids"] == list(result.omitted_unit_ids)
    assert payload["warnings"] == list(result.warnings)
    assert payload["runtime_provenance_records"] == []
    assert payload["metrics"]["aggregate_score"] == metrics.aggregate_score
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload


def test_resolved_selector_evidence_is_preserved_in_raw_record() -> None:
    """Raw records preserve original selector data and resolved evidence."""
    setup, result, metrics = _build_smoke_inputs()

    record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-selectors",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    payload = eval_results.eval_run_record_to_json(record)
    resolved_selectors = payload["resolved_selectors"]

    assert isinstance(resolved_selectors, list)
    first_selector = resolved_selectors[0]
    assert isinstance(first_selector, dict)
    assert first_selector["original_selector"] == {
        "kind": "symbol",
        "min_detail": "source",
        "expected_primary_capability_tier": None,
        "expect_attached_runtime_provenance": None,
        "qualified_name": "main.run",
        "role": "edit",
        "symbol_kind": "function",
        "rationale": "Primary edit target for the smoke oracle.",
    }
    assert first_selector["resolved_unit_id"] == "def:main.py:main.run"
    assert first_selector["resolved_file_path"] == "main.py"
    assert first_selector["resolved_span"] == {
        "start_line": 5,
        "start_column": 0,
        "end_line": 7,
        "end_column": 18,
    }
    assert first_selector["primary_capability_tier"] == "statically_proved"
    assert first_selector["primary_evidence_origin"] == "static_derivation_rule"
    assert first_selector["primary_replay_status"] == "deterministic_static"
    assert first_selector["has_attached_runtime_provenance"] is False
    assert first_selector["attached_runtime_provenance_record_ids"] == []


def test_structured_provider_metadata_is_preserved_in_raw_record() -> None:
    """Raw records preserve selected-unit and warning metadata for later slices."""
    setup, result, metrics = _build_smoke_inputs()

    record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-metadata",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    payload = eval_results.eval_run_record_to_json(record)
    provider_metadata = payload["provider_metadata"]

    assert isinstance(provider_metadata, dict)
    assert provider_metadata["selected_units"] == [
        {
            "unit_id": "def:main.py:main.run",
            "detail": "source",
            "token_count": 12,
            "basis": "pinned_obligation",
            "reason": "Primary edit target kept at source detail.",
            "edit_score": 1.0,
            "support_score": 0.2,
            "primary_capability_tier": "statically_proved",
            "primary_evidence_origin": "static_derivation_rule",
            "primary_replay_status": "deterministic_static",
            "has_attached_runtime_provenance": False,
            "attached_runtime_provenance_record_ids": [],
        },
        {
            "unit_id": "def:pkg/helpers.py:pkg.helpers.helper",
            "detail": "summary",
            "token_count": 6,
            "basis": "proven_dependency",
            "reason": "Direct support dependency for the edit target.",
            "edit_score": 0.3,
            "support_score": 0.9,
            "primary_capability_tier": "statically_proved",
            "primary_evidence_origin": "static_derivation_rule",
            "primary_replay_status": "deterministic_static",
            "has_attached_runtime_provenance": False,
            "attached_runtime_provenance_record_ids": [],
        },
    ]
    assert provider_metadata["warning_details"] == [
        {
            "code": "omitted_uncertainty",
            "unit_id": "frontier:call:main.py:7:4",
            "message": "Frontier uncertainty omitted under budget pressure.",
        },
        {
            "code": "omitted_uncertainty",
            "unit_id": "unsupported:import:main.py:1:0:1:*:_",
            "message": "Unsupported construct omitted under budget pressure.",
        },
    ]
    assert provider_metadata["unresolved_unit_ids"] == ["frontier:call:main.py:7:4"]
    assert provider_metadata["unsupported_unit_ids"] == [
        "unsupported:import:main.py:1:0:1:*:_"
    ]


def test_selector_tier_expectations_are_preserved_in_raw_record(
    tmp_path: Path,
) -> None:
    """Raw records keep optional selector tier expectations alongside evidence."""
    task_record = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    assert isinstance(task_record, dict)
    selectors = task_record["expected_selectors"]
    assert isinstance(selectors, list)
    first_selector = selectors[0]
    assert isinstance(first_selector, dict)
    first_selector["expected_primary_capability_tier"] = "statically_proved"
    first_selector["expect_attached_runtime_provenance"] = False
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps(task_record), encoding="utf-8")

    setup = setup_eval_oracle_task(
        task_path,
        REPO_ROOT / "evals" / "fixtures" / "oracle_smoke",
    )
    result = _smoke_provider_result(setup)
    metrics = score_eval_run(setup, result)

    payload = eval_results.eval_run_record_to_json(
        eval_results.build_eval_run_record(
            setup,
            result,
            metrics,
            run_id="run-expectations",
            git_commit="deadbeef",
            python_version="3.11.9",
            package_version=context_ir.__version__,
        )
    )
    resolved_selectors = payload["resolved_selectors"]
    assert isinstance(resolved_selectors, list)
    selector = resolved_selectors[0]
    assert isinstance(selector, dict)
    original_selector = selector["original_selector"]
    assert isinstance(original_selector, dict)
    assert original_selector["expected_primary_capability_tier"] == "statically_proved"
    assert original_selector["expect_attached_runtime_provenance"] is False


def test_fixture_file_hashes_are_deterministic_and_sorted() -> None:
    """Fixture hashes use deterministic UTF-8 content digests and sorted paths."""
    setup, result, metrics = _build_smoke_inputs()

    record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-hashes",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    payload = eval_results.eval_run_record_to_json(record)
    fixture_hashes = payload["fixture_file_hashes"]

    assert isinstance(fixture_hashes, dict)
    assert list(fixture_hashes) == sorted(fixture_hashes)
    assert fixture_hashes == _expected_fixture_hashes(setup.semantic_program.repo_root)


def test_fixture_file_hashes_use_raw_file_bytes_without_text_normalization(
    tmp_path: Path,
) -> None:
    """Fixture hashes preserve on-disk CRLF bytes rather than normalized text."""
    file_path = tmp_path / "crlf_fixture.py"
    raw_bytes = b"def target() -> int:\r\n    return 1\r\n"
    file_path.write_bytes(raw_bytes)

    hash_records = eval_results._fixture_file_hashes(tmp_path)

    assert hash_records == (
        eval_results.EvalFileHashRecord(
            file_path="crlf_fixture.py",
            sha256=hashlib.sha256(raw_bytes).hexdigest(),
        ),
    )
    normalized_hash = hashlib.sha256(
        file_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    assert hash_records[0].sha256 != normalized_hash


def test_append_eval_run_record_jsonl_writes_one_compact_json_object_per_line(
    tmp_path: Path,
) -> None:
    """JSONL append writes one compact JSON object per line."""
    setup, result, metrics = _build_smoke_inputs()
    record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-jsonl",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    ledger_path = tmp_path / "runs" / "raw.jsonl"

    eval_results.append_eval_run_record_jsonl(ledger_path, record)

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0]
    parsed = json.loads(lines[0])
    assert parsed == eval_results.eval_run_record_to_json(record)
    assert lines[0] == json.dumps(
        parsed,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_repeated_jsonl_append_preserves_previous_lines(tmp_path: Path) -> None:
    """Appending a second raw record preserves the first ledger entry."""
    setup, result, metrics = _build_smoke_inputs()
    ledger_path = tmp_path / "raw.jsonl"
    first_record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-001",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    second_record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-002",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )

    eval_results.append_eval_run_record_jsonl(ledger_path, first_record)
    eval_results.append_eval_run_record_jsonl(ledger_path, second_record)

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == eval_results.eval_run_record_to_json(first_record)
    assert json.loads(lines[1]) == eval_results.eval_run_record_to_json(second_record)


def test_build_and_serialize_do_not_mutate_inputs() -> None:
    """Raw record building and serialization leave accepted inputs unchanged."""
    setup, result, metrics = _build_smoke_inputs()
    setup_before = copy.deepcopy(setup)
    result_before = copy.deepcopy(result)
    metrics_before = copy.deepcopy(metrics)

    record = eval_results.build_eval_run_record(
        setup,
        result,
        metrics,
        run_id="run-immutability",
        git_commit="deadbeef",
        python_version="3.11.9",
        package_version=context_ir.__version__,
    )
    eval_results.eval_run_record_to_json(record)

    assert setup == setup_before
    assert result == result_before
    assert metrics == metrics_before


def test_eval_results_stay_internal_and_do_not_add_report_or_public_surfaces() -> None:
    """Raw result infrastructure stays internal and avoids report or claim surfaces."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "EvalRunRecord" not in context_ir.__all__
    assert not hasattr(context_ir, "EvalRunRecord")
    assert not hasattr(context_ir, "append_eval_run_record_jsonl")
    assert not hasattr(eval_results, "run_eval_matrix")
    assert not hasattr(eval_results, "build_markdown_report")

    record_fields = set(eval_results.EvalRunRecord.__dataclass_fields__)
    forbidden_fields = {
        "markdown_report",
        "category_rollups",
        "public_claims",
        "raw_summary",
        "matrix_results",
    }

    assert forbidden_fields.isdisjoint(record_fields)
