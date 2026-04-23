"""Eval oracle foundation tests."""

from __future__ import annotations

import copy
import json
import textwrap
from pathlib import Path
from typing import cast

import pytest

import context_ir
import context_ir.eval_oracles as eval_oracles
from context_ir.analyzer import analyze_repository
from context_ir.eval_oracles import (
    EvalOracleResolutionError,
    EvalOracleSchemaError,
    EvalOracleTask,
    FrontierOracleSelector,
    SymbolOracleSelector,
    UnsupportedOracleSelector,
    load_eval_oracle_task,
    resolve_eval_oracle_task,
    setup_eval_oracle_task,
)
from context_ir.semantic_types import (
    CapabilityTier,
    DownstreamVisibility,
    EvidenceOriginKind,
    ReferenceContext,
    ReplayStatus,
    RepositorySnapshotBasis,
    ResolvedSymbolKind,
    RuntimeAttachmentLink,
    SemanticProgram,
    SemanticProvenanceRecord,
    SemanticSubjectKind,
    SourceSpan,
    UnresolvedReasonCode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json"
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_smoke"
PROBE_TASK_PATH = (
    REPO_ROOT / "evals" / "tasks" / "oracle_signal_dynamic_import_probe.json"
)
HASATTR_PROBE_TASK_PATH = (
    REPO_ROOT / "evals" / "tasks" / "oracle_signal_hasattr_probe.json"
)


def _load_smoke_task_record() -> dict[str, object]:
    """Load the smoke task JSON as a mutable object record."""
    raw: object = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return cast(dict[str, object], raw)


def _selector_record(
    task_record: dict[str, object],
    index: int,
) -> dict[str, object]:
    """Return one mutable selector record from a smoke task copy."""
    selectors = task_record["expected_selectors"]
    assert isinstance(selectors, list)
    selector = selectors[index]
    assert isinstance(selector, dict)
    return cast(dict[str, object], selector)


def _write_task_record(
    tmp_path: Path,
    task_record: dict[str, object],
) -> Path:
    """Write a task record copy to a temporary JSON file."""
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps(task_record), encoding="utf-8")
    return task_path


def test_task_json_loads_into_typed_selector_dataclasses() -> None:
    """The durable task asset loads into typed selector records."""
    task = load_eval_oracle_task(TASK_PATH)

    assert task.task_id == "oracle_smoke"
    assert task.fixture_id == "oracle_smoke"
    assert len(task.expected_selectors) == 4
    assert isinstance(task.expected_selectors[0], SymbolOracleSelector)
    assert isinstance(task.expected_selectors[1], SymbolOracleSelector)
    assert isinstance(task.expected_selectors[2], FrontierOracleSelector)
    assert isinstance(task.expected_selectors[3], UnsupportedOracleSelector)

    edit_selector = task.expected_selectors[0]
    frontier_selector = task.expected_selectors[2]
    assert isinstance(edit_selector, SymbolOracleSelector)
    assert edit_selector.qualified_name == "main.run"
    assert edit_selector.role == "edit"
    assert edit_selector.symbol_kind is ResolvedSymbolKind.FUNCTION
    assert edit_selector.expected_primary_capability_tier is None
    assert edit_selector.expect_attached_runtime_provenance is None
    assert isinstance(frontier_selector, FrontierOracleSelector)
    assert frontier_selector.context is ReferenceContext.CALL
    assert frontier_selector.reason_code is UnresolvedReasonCode.UNRESOLVED_NAME
    assert frontier_selector.expected_primary_capability_tier is None
    assert frontier_selector.expect_attached_runtime_provenance is None


def test_selector_tier_expectations_load_when_present(tmp_path: Path) -> None:
    """Durable task JSON accepts optional selector tier expectation fields."""
    task_record = _load_smoke_task_record()
    selector_record = _selector_record(task_record, 0)
    selector_record["expected_primary_capability_tier"] = "statically_proved"
    selector_record["expect_attached_runtime_provenance"] = False
    task_path = _write_task_record(tmp_path, task_record)

    task = load_eval_oracle_task(task_path)
    selector = task.expected_selectors[0]

    assert isinstance(selector, SymbolOracleSelector)
    assert selector.expected_primary_capability_tier is CapabilityTier.STATICALLY_PROVED
    assert selector.expect_attached_runtime_provenance is False


def test_generated_unit_ids_are_not_accepted_as_durable_oracle_fields(
    tmp_path: Path,
) -> None:
    """Durable task JSON rejects generated runtime unit identifiers."""
    task_record = _load_smoke_task_record()
    _selector_record(task_record, 0)["unit_id"] = "def:main.py:main.run"
    task_path = _write_task_record(tmp_path, task_record)

    with pytest.raises(EvalOracleSchemaError, match="generated runtime identifier"):
        load_eval_oracle_task(task_path)


def test_unknown_top_level_task_fields_are_rejected(tmp_path: Path) -> None:
    """Durable task JSON rejects unknown top-level fields."""
    task_record = _load_smoke_task_record()
    task_record["qualifiedName"] = "main.run"
    task_path = _write_task_record(tmp_path, task_record)

    with pytest.raises(
        EvalOracleSchemaError,
        match=r"unknown field 'qualifiedName'",
    ):
        load_eval_oracle_task(task_path)


def test_unknown_symbol_selector_fields_are_rejected(tmp_path: Path) -> None:
    """Symbol selectors reject unknown fields."""
    task_record = _load_smoke_task_record()
    _selector_record(task_record, 0)["qualifiedName"] = "main.run"
    task_path = _write_task_record(tmp_path, task_record)

    with pytest.raises(
        EvalOracleSchemaError,
        match=r"unknown field 'qualifiedName'",
    ):
        load_eval_oracle_task(task_path)


def test_unknown_frontier_selector_fields_are_rejected(tmp_path: Path) -> None:
    """Frontier selectors reject unknown fields."""
    task_record = _load_smoke_task_record()
    _selector_record(task_record, 2)["min_dtail"] = "source"
    task_path = _write_task_record(tmp_path, task_record)

    with pytest.raises(
        EvalOracleSchemaError,
        match=r"unknown field 'min_dtail'",
    ):
        load_eval_oracle_task(task_path)


def test_unknown_unsupported_selector_fields_are_rejected(tmp_path: Path) -> None:
    """Unsupported selectors reject unknown fields."""
    task_record = _load_smoke_task_record()
    _selector_record(task_record, 3)["constructText"] = "import"
    task_path = _write_task_record(tmp_path, task_record)

    with pytest.raises(
        EvalOracleSchemaError,
        match=r"unknown field 'constructText'",
    ):
        load_eval_oracle_task(task_path)


def test_oracle_smoke_task_resolves_all_selector_kinds_through_analyzer() -> None:
    """The fixture task resolves symbol, frontier, and unsupported selectors."""
    setup = setup_eval_oracle_task(TASK_PATH)

    assert setup.task.task_id == "oracle_smoke"
    assert isinstance(setup.semantic_program, SemanticProgram)
    resolved_by_kind = {
        resolved.selector.kind: resolved for resolved in setup.resolved_selectors
    }

    symbol_records = [
        resolved
        for resolved in setup.resolved_selectors
        if resolved.selector.kind == "symbol"
    ]
    assert {record.resolved_unit_id for record in symbol_records} == {
        "def:main.py:main.run",
        "def:pkg/helpers.py:pkg.helpers.helper",
    }
    for resolved in setup.resolved_selectors:
        assert resolved.resolution_status == "resolved"
        assert resolved.resolved_unit_id is not None
        assert resolved.resolved_file_path is not None
        assert isinstance(resolved.resolved_span, SourceSpan)
        assert resolved.failure_reason is None
        assert resolved.candidate_count == 1
        assert resolved.selector in setup.task.expected_selectors

    symbol_record = symbol_records[0]
    assert symbol_record.primary_capability_tier is CapabilityTier.STATICALLY_PROVED
    assert (
        symbol_record.primary_evidence_origin
        is EvidenceOriginKind.STATIC_DERIVATION_RULE
    )
    assert symbol_record.primary_replay_status is ReplayStatus.DETERMINISTIC_STATIC
    assert symbol_record.has_attached_runtime_provenance is False
    assert symbol_record.attached_runtime_provenance_record_ids == ()
    assert resolved_by_kind["frontier"].resolved_unit_id == "frontier:call:main.py:7:4"
    assert (
        resolved_by_kind["frontier"].primary_capability_tier
        is CapabilityTier.HEURISTIC_FRONTIER
    )
    assert (
        resolved_by_kind["frontier"].primary_evidence_origin
        is EvidenceOriginKind.HEURISTIC_RULE
    )
    assert (
        resolved_by_kind["frontier"].primary_replay_status
        is ReplayStatus.NON_PROOF_HEURISTIC
    )
    assert resolved_by_kind["frontier"].has_attached_runtime_provenance is False
    assert (
        resolved_by_kind["unsupported"].resolved_unit_id
        == "unsupported:import:main.py:1:0:1:*:_"
    )
    assert (
        resolved_by_kind["unsupported"].primary_capability_tier
        is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert (
        resolved_by_kind["unsupported"].primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert (
        resolved_by_kind["unsupported"].primary_replay_status
        is ReplayStatus.OPAQUE_BOUNDARY
    )
    assert resolved_by_kind["unsupported"].has_attached_runtime_provenance is False


def test_resolved_selector_snapshot_captures_attached_runtime_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolved selector evidence keeps additive runtime-backed attachments."""
    task = load_eval_oracle_task(TASK_PATH)
    base_program = analyze_repository(FIXTURE_ROOT)
    symbol = base_program.resolved_symbols["def:main.py:main.run"]
    augmented_program = SemanticProgram(
        repo_root=base_program.repo_root,
        syntax=base_program.syntax,
        supported_subset=base_program.supported_subset,
        resolved_symbols=base_program.resolved_symbols,
        bindings=base_program.bindings,
        resolved_imports=base_program.resolved_imports,
        dataclass_models=base_program.dataclass_models,
        dataclass_fields=base_program.dataclass_fields,
        resolved_references=base_program.resolved_references,
        proven_dependencies=base_program.proven_dependencies,
        unresolved_frontier=base_program.unresolved_frontier,
        unsupported_constructs=base_program.unsupported_constructs,
        provenance_records=[
            SemanticProvenanceRecord(
                record_id="prov:symbol:runtime:run",
                subject_kind=SemanticSubjectKind.SYMBOL,
                subject_id=symbol.symbol_id,
                capability_tier=CapabilityTier.RUNTIME_BACKED,
                evidence_origin=EvidenceOriginKind.RUNTIME_PROBE_IDENTITY,
                origin_detail="Observed callable identity at runtime.",
                replay_status=ReplayStatus.REPRODUCIBLE_RUNTIME,
                repository_snapshot_basis=RepositorySnapshotBasis(
                    snapshot_kind="git_commit",
                    snapshot_id="abc1234",
                ),
                attachment_links=(
                    RuntimeAttachmentLink(
                        attachment_id="artifact:runtime:run",
                        attachment_role="probe_result",
                    ),
                ),
                subject_sites=(symbol.definition_site,),
                downstream_visibility=(DownstreamVisibility.COMPILE,),
            )
        ],
        diagnostics=base_program.diagnostics,
    )

    monkeypatch.setattr(
        eval_oracles,
        "analyze_repository",
        lambda repo_root: augmented_program,
    )

    setup = resolve_eval_oracle_task(task, FIXTURE_ROOT)
    resolved_symbol = setup.resolved_selectors[0]

    assert resolved_symbol.resolved_unit_id == "def:main.py:main.run"
    assert resolved_symbol.primary_capability_tier is CapabilityTier.STATICALLY_PROVED
    assert (
        resolved_symbol.primary_evidence_origin
        is EvidenceOriginKind.STATIC_DERIVATION_RULE
    )
    assert resolved_symbol.primary_replay_status is ReplayStatus.DETERMINISTIC_STATIC
    assert resolved_symbol.has_attached_runtime_provenance is True
    assert resolved_symbol.attached_runtime_provenance_record_ids == (
        "prov:symbol:runtime:run",
    )


def test_setup_eval_oracle_task_loads_dynamic_import_runtime_probe_when_present() -> (
    None
):
    """Fixture-local dynamic-import probes attach additive runtime provenance."""
    setup = setup_eval_oracle_task(PROBE_TASK_PATH)

    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.load_weather_plugin",
        "def:main.py:main.render_probe_digest",
        "unsupported:call:main.py:5:13",
    ]
    unsupported = setup.resolved_selectors[2]
    selector = unsupported.selector

    assert isinstance(selector, UnsupportedOracleSelector)
    assert (
        selector.expected_primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert selector.expect_attached_runtime_provenance is True
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_setup_eval_oracle_task_loads_hasattr_runtime_probe_when_present() -> None:
    """Fixture-local ``hasattr`` probes attach additive runtime provenance."""
    setup = setup_eval_oracle_task(HASATTR_PROBE_TASK_PATH)

    assert [resolved.resolved_unit_id for resolved in setup.resolved_selectors] == [
        "def:main.py:main.probe_attribute",
        "def:main.py:main.render_probe_digest",
        "unsupported:call:main.py:2:11",
    ]
    unsupported = setup.resolved_selectors[2]
    selector = unsupported.selector

    assert isinstance(selector, UnsupportedOracleSelector)
    assert (
        selector.expected_primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    )
    assert selector.expect_attached_runtime_provenance is True
    assert unsupported.primary_capability_tier is CapabilityTier.UNSUPPORTED_OPAQUE
    assert (
        unsupported.primary_evidence_origin
        is EvidenceOriginKind.UNSUPPORTED_REASON_CODE
    )
    assert unsupported.primary_replay_status is ReplayStatus.OPAQUE_BOUNDARY
    assert unsupported.has_attached_runtime_provenance is True
    assert unsupported.attached_runtime_provenance_record_ids


def test_resolve_eval_oracle_task_calls_analyze_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Task resolution uses the accepted public semantic analyzer."""
    task = load_eval_oracle_task(TASK_PATH)
    program = analyze_repository(FIXTURE_ROOT)
    calls: list[Path] = []

    def fake_analyze(repo_root: Path | str) -> SemanticProgram:
        calls.append(Path(repo_root))
        return program

    monkeypatch.setattr(eval_oracles, "analyze_repository", fake_analyze)

    setup = resolve_eval_oracle_task(task, FIXTURE_ROOT)

    assert setup.semantic_program is program
    assert calls == [FIXTURE_ROOT]


def test_unresolved_selectors_fail_setup_loudly() -> None:
    """A selector with no semantic match raises an explicit setup failure."""
    task = EvalOracleTask(
        task_id="missing_symbol",
        fixture_id="oracle_smoke",
        expected_selectors=(
            SymbolOracleSelector(
                kind="symbol",
                qualified_name="main.missing",
                role="edit",
                min_detail="source",
            ),
        ),
    )

    with pytest.raises(EvalOracleResolutionError, match="failed selector setup") as exc:
        resolve_eval_oracle_task(task, FIXTURE_ROOT)

    assert len(exc.value.failures) == 1
    failure = exc.value.failures[0]
    assert failure.resolution_status == "unresolved"
    assert failure.candidate_count == 0
    assert failure.resolved_unit_id is None
    assert failure.failure_reason == "selector matched no candidates"


def test_ambiguous_selectors_fail_setup_loudly(tmp_path: Path) -> None:
    """Duplicate qualified-name matches are rejected as ambiguous setup."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def target() -> None:
                return None

            def target() -> None:
                return None
            """
        ).lstrip(),
        encoding="utf-8",
    )
    task = EvalOracleTask(
        task_id="ambiguous_symbol",
        fixture_id="inline",
        expected_selectors=(
            SymbolOracleSelector(
                kind="symbol",
                qualified_name="main.target",
                role="edit",
                min_detail="source",
            ),
        ),
    )

    with pytest.raises(EvalOracleResolutionError, match="ambiguous") as exc:
        resolve_eval_oracle_task(task, tmp_path)

    failure = exc.value.failures[0]
    assert failure.resolution_status == "ambiguous"
    assert failure.candidate_count == 2
    assert failure.resolved_unit_id is None
    assert len(failure.candidate_summaries) == 2
    assert all("main.target" in summary for summary in failure.candidate_summaries)


def test_selector_resolution_does_not_mutate_semantic_program(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolving selectors reads but does not mutate analyzer output."""
    task = load_eval_oracle_task(TASK_PATH)
    program = analyze_repository(FIXTURE_ROOT)
    original_symbols = copy.deepcopy(program.resolved_symbols)
    original_frontier = copy.deepcopy(program.unresolved_frontier)
    original_unsupported = copy.deepcopy(program.unsupported_constructs)

    def fake_analyze(repo_root: Path | str) -> SemanticProgram:
        assert Path(repo_root) == FIXTURE_ROOT
        return program

    monkeypatch.setattr(eval_oracles, "analyze_repository", fake_analyze)

    setup = resolve_eval_oracle_task(task, FIXTURE_ROOT)

    assert setup.semantic_program is program
    assert program.resolved_symbols == original_symbols
    assert program.unresolved_frontier == original_frontier
    assert program.unsupported_constructs == original_unsupported


def test_eval_oracle_slice_does_not_extend_public_package_or_other_machinery() -> None:
    """This slice stays internal and does not add provider or result machinery."""
    assert not hasattr(context_ir, "load_eval_oracle_task")
    assert not hasattr(context_ir, "setup_eval_oracle_task")

    public_names = {
        name.lower() for name in dir(eval_oracles) if not name.startswith("_")
    }
    forbidden_fragments = {"baseline", "jsonl", "metric", "provider", "report", "score"}
    assert not any(
        fragment in public_name
        for fragment in forbidden_fragments
        for public_name in public_names
    )
