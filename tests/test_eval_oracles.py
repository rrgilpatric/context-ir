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
    ReferenceContext,
    ResolvedSymbolKind,
    SemanticProgram,
    SourceSpan,
    UnresolvedReasonCode,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = REPO_ROOT / "evals" / "tasks" / "oracle_smoke.json"
FIXTURE_ROOT = REPO_ROOT / "evals" / "fixtures" / "oracle_smoke"


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
    assert isinstance(frontier_selector, FrontierOracleSelector)
    assert frontier_selector.context is ReferenceContext.CALL
    assert frontier_selector.reason_code is UnresolvedReasonCode.UNRESOLVED_NAME


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

    assert resolved_by_kind["frontier"].resolved_unit_id == "frontier:call:main.py:7:4"
    assert (
        resolved_by_kind["unsupported"].resolved_unit_id
        == "unsupported:import:main.py:1:0:1:*:_"
    )


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
