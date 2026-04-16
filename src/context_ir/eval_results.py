"""Deterministic raw eval run record builders and JSONL persistence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from context_ir.eval_metrics import EvalRunMetrics
from context_ir.eval_oracles import (
    EvalOracleSetup,
    OracleSelector,
    ResolvedOracleSelector,
)
from context_ir.eval_providers import (
    EvalProviderConfig,
    EvalProviderMetadata,
    EvalProviderResult,
    EvalProviderWarning,
    EvalSelectedUnit,
    LexicalFileScore,
)
from context_ir.semantic_types import SourceSpan


@dataclass(frozen=True)
class EvalFileHashRecord:
    """Deterministic content hash for one fixture source file."""

    file_path: str
    sha256: str


@dataclass(frozen=True)
class EvalProviderConfigRecord:
    """JSON-safe provider configuration captured with one eval run."""

    max_candidates: int | None
    seed_count: int | None
    diagnostic_only: bool


@dataclass(frozen=True)
class EvalLexicalFileScoreRecord:
    """Structured lexical baseline metadata preserved for raw ledgers."""

    file_path: str
    score: float
    token_count: int


@dataclass(frozen=True)
class EvalSelectedUnitRecord:
    """Structured selected-unit metadata preserved for raw ledgers."""

    unit_id: str
    detail: str
    token_count: int
    basis: str
    reason: str | None
    edit_score: float | None
    support_score: float | None


@dataclass(frozen=True)
class EvalProviderWarningRecord:
    """Structured provider warning metadata preserved for raw ledgers."""

    code: str
    unit_id: str | None
    message: str


@dataclass(frozen=True)
class EvalProviderMetadataRecord:
    """JSON-safe structured provider metadata for one eval run."""

    diagnostic_only: bool
    candidate_files: tuple[str, ...]
    omitted_candidate_files: tuple[str, ...]
    lexical_scores: tuple[EvalLexicalFileScoreRecord, ...]
    selected_units: tuple[EvalSelectedUnitRecord, ...]
    warning_details: tuple[EvalProviderWarningRecord, ...]
    unresolved_unit_ids: tuple[str, ...]
    unsupported_unit_ids: tuple[str, ...]
    syntax_diagnostic_ids: tuple[str, ...]
    semantic_diagnostic_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvalSourceSpanRecord:
    """JSON-safe source span evidence preserved for one resolved selector."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class EvalOriginalSelectorRecord:
    """JSON-safe durable selector record captured alongside resolution evidence."""

    kind: str
    min_detail: str
    qualified_name: str | None = None
    role: str | None = None
    symbol_kind: str | None = None
    file_path: str | None = None
    access_text: str | None = None
    context: str | None = None
    reason_code: str | None = None
    enclosing_qualified_name: str | None = None
    source_snippet: str | None = None
    construct_text: str | None = None
    rationale: str | None = None


@dataclass(frozen=True)
class EvalResolvedSelectorRecord:
    """Resolved durable oracle selector evidence captured for one raw run."""

    original_selector: EvalOriginalSelectorRecord
    resolution_status: str
    resolved_unit_id: str | None
    resolved_file_path: str | None
    resolved_span: EvalSourceSpanRecord | None
    failure_reason: str | None
    candidate_count: int
    candidate_summaries: tuple[str, ...]


@dataclass(frozen=True)
class EvalRunMetricRecord:
    """JSON-safe metric outputs for one scored eval provider run."""

    provider_name: str
    task_id: str
    budget: int
    budget_compliant: bool
    edit_coverage: float
    support_coverage: float | None
    representation_adequacy: float
    uncertainty_honesty: float | None
    credited_relevant_tokens: int
    noise_tokens: int
    noise_ratio: float
    noise_efficiency: float
    aggregate_score: float
    total_expected_edit_selectors: int
    adequate_edit_selectors: int
    total_expected_support_selectors: int
    adequate_support_selectors: int
    total_expected_uncertainty_selectors: int
    represented_expected_selector_count: int
    too_shallow_selector_ids: tuple[str, ...]
    omitted_expected_uncertainty_ids: tuple[str, ...]
    selected_matched_selector_ids: tuple[str, ...]


@dataclass(frozen=True)
class EvalRunRecord:
    """Deterministic raw result record for one accepted eval run."""

    spec_version: str
    run_id: str
    task_id: str
    fixture_id: str
    fixture_repo_root: str
    fixture_file_hashes: tuple[EvalFileHashRecord, ...]
    git_commit: str
    python_version: str
    package_version: str
    provider_name: str
    provider_algorithm_version: str
    provider_config: EvalProviderConfigRecord
    query: str
    budget: int
    total_tokens: int
    document: str
    selected_files: tuple[str, ...]
    selected_unit_ids: tuple[str, ...]
    omitted_unit_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    provider_metadata: EvalProviderMetadataRecord
    resolved_selectors: tuple[EvalResolvedSelectorRecord, ...]
    metrics: EvalRunMetricRecord


def build_eval_run_record(
    setup: EvalOracleSetup,
    result: EvalProviderResult,
    metrics: EvalRunMetrics,
    *,
    run_id: str,
    git_commit: str,
    python_version: str,
    package_version: str,
    spec_version: str = "v1",
) -> EvalRunRecord:
    """Build one deterministic raw eval result record from accepted inputs."""
    if not run_id:
        raise ValueError("run_id must be non-empty")
    if not git_commit:
        raise ValueError("git_commit must be non-empty")
    if not python_version:
        raise ValueError("python_version must be non-empty")
    if not package_version:
        raise ValueError("package_version must be non-empty")
    if not spec_version:
        raise ValueError("spec_version must be non-empty")
    if setup.task.task_id != result.task_id:
        raise ValueError("oracle setup task_id must match provider result task_id")
    if setup.task.task_id != metrics.task_id:
        raise ValueError("oracle setup task_id must match metric task_id")
    if result.provider_name != metrics.provider_name:
        raise ValueError("provider result name must match metric provider name")
    if result.budget != metrics.budget:
        raise ValueError("provider result budget must match metric budget")

    repo_root = setup.semantic_program.repo_root
    return EvalRunRecord(
        spec_version=spec_version,
        run_id=run_id,
        task_id=setup.task.task_id,
        fixture_id=setup.task.fixture_id,
        fixture_repo_root=str(repo_root),
        fixture_file_hashes=_fixture_file_hashes(repo_root),
        git_commit=git_commit,
        python_version=python_version,
        package_version=package_version,
        provider_name=result.provider_name,
        provider_algorithm_version=result.provider_algorithm_version,
        provider_config=_provider_config_record(result.provider_config),
        query=result.query,
        budget=result.budget,
        total_tokens=result.total_tokens,
        document=result.document,
        selected_files=result.selected_files,
        selected_unit_ids=result.selected_unit_ids,
        omitted_unit_ids=result.omitted_unit_ids,
        warnings=result.warnings,
        provider_metadata=_provider_metadata_record(result.metadata),
        resolved_selectors=tuple(
            _resolved_selector_record(record) for record in setup.resolved_selectors
        ),
        metrics=_metric_record(metrics),
    )


def eval_run_record_to_json(record: EvalRunRecord) -> dict[str, object]:
    """Serialize one raw eval record into a stable JSON-safe object."""
    return {
        "spec_version": record.spec_version,
        "run_id": record.run_id,
        "task_id": record.task_id,
        "fixture_id": record.fixture_id,
        "fixture_repo_root": record.fixture_repo_root,
        "fixture_file_hashes": {
            file_record.file_path: file_record.sha256
            for file_record in record.fixture_file_hashes
        },
        "git_commit": record.git_commit,
        "python_version": record.python_version,
        "package_version": record.package_version,
        "provider_name": record.provider_name,
        "provider_algorithm_version": record.provider_algorithm_version,
        "provider_config": _provider_config_to_json(record.provider_config),
        "query": record.query,
        "budget": record.budget,
        "total_tokens": record.total_tokens,
        "document": record.document,
        "selected_files": list(record.selected_files),
        "selected_unit_ids": list(record.selected_unit_ids),
        "omitted_unit_ids": list(record.omitted_unit_ids),
        "warnings": list(record.warnings),
        "provider_metadata": _provider_metadata_to_json(record.provider_metadata),
        "resolved_selectors": [
            _resolved_selector_to_json(selector_record)
            for selector_record in record.resolved_selectors
        ],
        "metrics": _metrics_to_json(record.metrics),
    }


def append_eval_run_record_jsonl(path: Path | str, record: EvalRunRecord) -> None:
    """Append one compact JSON-safe raw eval record to a JSONL ledger."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        eval_run_record_to_json(record),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    with target.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.write("\n")


def _fixture_file_hashes(repo_root: Path) -> tuple[EvalFileHashRecord, ...]:
    """Return deterministic SHA-256 hashes for fixture Python files."""
    return tuple(
        EvalFileHashRecord(
            file_path=relative_path,
            sha256=hashlib.sha256(file_path.read_bytes()).hexdigest(),
        )
        for relative_path, file_path in _iter_fixture_python_files(repo_root)
    )


def _iter_fixture_python_files(
    repo_root: Path,
) -> tuple[tuple[str, Path], ...]:
    """Return sorted repository-relative Python files below one fixture root."""
    files = []
    for file_path in repo_root.rglob("*.py"):
        if not file_path.is_file():
            continue
        relative_path = file_path.relative_to(repo_root).as_posix()
        files.append((relative_path, file_path))
    files.sort(key=lambda item: item[0])
    return tuple(files)


def _provider_config_record(config: EvalProviderConfig) -> EvalProviderConfigRecord:
    """Return the JSON-safe provider configuration record."""
    return EvalProviderConfigRecord(
        max_candidates=config.max_candidates,
        seed_count=config.seed_count,
        diagnostic_only=config.diagnostic_only,
    )


def _provider_metadata_record(
    metadata: EvalProviderMetadata,
) -> EvalProviderMetadataRecord:
    """Return JSON-safe structured provider metadata."""
    return EvalProviderMetadataRecord(
        diagnostic_only=metadata.diagnostic_only,
        candidate_files=metadata.candidate_files,
        omitted_candidate_files=metadata.omitted_candidate_files,
        lexical_scores=tuple(
            _lexical_score_record(score) for score in metadata.lexical_scores
        ),
        selected_units=tuple(
            _selected_unit_record(selected_unit)
            for selected_unit in metadata.selected_units
        ),
        warning_details=tuple(
            _warning_record(warning) for warning in metadata.warning_details
        ),
        unresolved_unit_ids=metadata.unresolved_unit_ids,
        unsupported_unit_ids=metadata.unsupported_unit_ids,
        syntax_diagnostic_ids=metadata.syntax_diagnostic_ids,
        semantic_diagnostic_ids=metadata.semantic_diagnostic_ids,
    )


def _lexical_score_record(score: LexicalFileScore) -> EvalLexicalFileScoreRecord:
    """Return one JSON-safe lexical score metadata record."""
    return EvalLexicalFileScoreRecord(
        file_path=score.file_path,
        score=score.score,
        token_count=score.token_count,
    )


def _selected_unit_record(selected_unit: EvalSelectedUnit) -> EvalSelectedUnitRecord:
    """Return one JSON-safe selected-unit metadata record."""
    return EvalSelectedUnitRecord(
        unit_id=selected_unit.unit_id,
        detail=selected_unit.detail,
        token_count=selected_unit.token_count,
        basis=selected_unit.basis,
        reason=selected_unit.reason,
        edit_score=selected_unit.edit_score,
        support_score=selected_unit.support_score,
    )


def _warning_record(warning: EvalProviderWarning) -> EvalProviderWarningRecord:
    """Return one JSON-safe provider warning metadata record."""
    return EvalProviderWarningRecord(
        code=warning.code,
        unit_id=warning.unit_id,
        message=warning.message,
    )


def _resolved_selector_record(
    resolved_selector: ResolvedOracleSelector,
) -> EvalResolvedSelectorRecord:
    """Return JSON-safe evidence for one resolved durable oracle selector."""
    span = resolved_selector.resolved_span
    return EvalResolvedSelectorRecord(
        original_selector=_original_selector_record(resolved_selector.selector),
        resolution_status=resolved_selector.resolution_status,
        resolved_unit_id=resolved_selector.resolved_unit_id,
        resolved_file_path=resolved_selector.resolved_file_path,
        resolved_span=None if span is None else _span_record(span),
        failure_reason=resolved_selector.failure_reason,
        candidate_count=resolved_selector.candidate_count,
        candidate_summaries=resolved_selector.candidate_summaries,
    )


def _original_selector_record(selector: OracleSelector) -> EvalOriginalSelectorRecord:
    """Return one JSON-safe durable oracle selector record."""
    if selector.kind == "symbol":
        symbol_kind = None
        if selector.symbol_kind is not None:
            symbol_kind = selector.symbol_kind.value
        return EvalOriginalSelectorRecord(
            kind=selector.kind,
            min_detail=selector.min_detail,
            qualified_name=selector.qualified_name,
            role=selector.role,
            symbol_kind=symbol_kind,
            rationale=selector.rationale,
        )

    if selector.kind == "frontier":
        return EvalOriginalSelectorRecord(
            kind=selector.kind,
            min_detail=selector.min_detail,
            file_path=selector.file_path,
            access_text=selector.access_text,
            context=selector.context.value,
            reason_code=selector.reason_code.value,
            enclosing_qualified_name=selector.enclosing_qualified_name,
            source_snippet=selector.source_snippet,
            rationale=selector.rationale,
        )

    return EvalOriginalSelectorRecord(
        kind=selector.kind,
        min_detail=selector.min_detail,
        file_path=selector.file_path,
        reason_code=selector.reason_code.value,
        enclosing_qualified_name=selector.enclosing_qualified_name,
        source_snippet=selector.source_snippet,
        construct_text=selector.construct_text,
        rationale=selector.rationale,
    )


def _span_record(span: SourceSpan) -> EvalSourceSpanRecord:
    """Return one JSON-safe source span record."""
    return EvalSourceSpanRecord(
        start_line=span.start_line,
        start_column=span.start_column,
        end_line=span.end_line,
        end_column=span.end_column,
    )


def _metric_record(metrics: EvalRunMetrics) -> EvalRunMetricRecord:
    """Return JSON-safe metric outputs for one eval run."""
    return EvalRunMetricRecord(
        provider_name=metrics.provider_name,
        task_id=metrics.task_id,
        budget=metrics.budget,
        budget_compliant=metrics.budget_compliant,
        edit_coverage=metrics.edit_coverage,
        support_coverage=metrics.support_coverage,
        representation_adequacy=metrics.representation_adequacy,
        uncertainty_honesty=metrics.uncertainty_honesty,
        credited_relevant_tokens=metrics.credited_relevant_tokens,
        noise_tokens=metrics.noise_tokens,
        noise_ratio=metrics.noise_ratio,
        noise_efficiency=metrics.noise_efficiency,
        aggregate_score=metrics.aggregate_score,
        total_expected_edit_selectors=metrics.total_expected_edit_selectors,
        adequate_edit_selectors=metrics.adequate_edit_selectors,
        total_expected_support_selectors=metrics.total_expected_support_selectors,
        adequate_support_selectors=metrics.adequate_support_selectors,
        total_expected_uncertainty_selectors=metrics.total_expected_uncertainty_selectors,
        represented_expected_selector_count=metrics.represented_expected_selector_count,
        too_shallow_selector_ids=metrics.too_shallow_selector_ids,
        omitted_expected_uncertainty_ids=metrics.omitted_expected_uncertainty_ids,
        selected_matched_selector_ids=metrics.selected_matched_selector_ids,
    )


def _provider_config_to_json(config: EvalProviderConfigRecord) -> dict[str, object]:
    """Return one JSON-safe provider configuration object."""
    return {
        "max_candidates": config.max_candidates,
        "seed_count": config.seed_count,
        "diagnostic_only": config.diagnostic_only,
    }


def _provider_metadata_to_json(
    metadata: EvalProviderMetadataRecord,
) -> dict[str, object]:
    """Return one JSON-safe structured provider metadata object."""
    return {
        "diagnostic_only": metadata.diagnostic_only,
        "candidate_files": list(metadata.candidate_files),
        "omitted_candidate_files": list(metadata.omitted_candidate_files),
        "lexical_scores": [
            {
                "file_path": score.file_path,
                "score": score.score,
                "token_count": score.token_count,
            }
            for score in metadata.lexical_scores
        ],
        "selected_units": [
            {
                "unit_id": unit.unit_id,
                "detail": unit.detail,
                "token_count": unit.token_count,
                "basis": unit.basis,
                "reason": unit.reason,
                "edit_score": unit.edit_score,
                "support_score": unit.support_score,
            }
            for unit in metadata.selected_units
        ],
        "warning_details": [
            {
                "code": warning.code,
                "unit_id": warning.unit_id,
                "message": warning.message,
            }
            for warning in metadata.warning_details
        ],
        "unresolved_unit_ids": list(metadata.unresolved_unit_ids),
        "unsupported_unit_ids": list(metadata.unsupported_unit_ids),
        "syntax_diagnostic_ids": list(metadata.syntax_diagnostic_ids),
        "semantic_diagnostic_ids": list(metadata.semantic_diagnostic_ids),
    }


def _resolved_selector_to_json(
    selector_record: EvalResolvedSelectorRecord,
) -> dict[str, object]:
    """Return one JSON-safe resolved selector evidence object."""
    return {
        "original_selector": _original_selector_to_json(
            selector_record.original_selector
        ),
        "resolution_status": selector_record.resolution_status,
        "resolved_unit_id": selector_record.resolved_unit_id,
        "resolved_file_path": selector_record.resolved_file_path,
        "resolved_span": (
            None
            if selector_record.resolved_span is None
            else _span_to_json(selector_record.resolved_span)
        ),
        "failure_reason": selector_record.failure_reason,
        "candidate_count": selector_record.candidate_count,
        "candidate_summaries": list(selector_record.candidate_summaries),
    }


def _original_selector_to_json(
    selector: EvalOriginalSelectorRecord,
) -> dict[str, object]:
    """Return one JSON-safe original selector object without null-only fields."""
    selector_json: dict[str, object] = {
        "kind": selector.kind,
        "min_detail": selector.min_detail,
    }
    if selector.qualified_name is not None:
        selector_json["qualified_name"] = selector.qualified_name
    if selector.role is not None:
        selector_json["role"] = selector.role
    if selector.symbol_kind is not None:
        selector_json["symbol_kind"] = selector.symbol_kind
    if selector.file_path is not None:
        selector_json["file_path"] = selector.file_path
    if selector.access_text is not None:
        selector_json["access_text"] = selector.access_text
    if selector.context is not None:
        selector_json["context"] = selector.context
    if selector.reason_code is not None:
        selector_json["reason_code"] = selector.reason_code
    if selector.enclosing_qualified_name is not None:
        selector_json["enclosing_qualified_name"] = selector.enclosing_qualified_name
    if selector.source_snippet is not None:
        selector_json["source_snippet"] = selector.source_snippet
    if selector.construct_text is not None:
        selector_json["construct_text"] = selector.construct_text
    if selector.rationale is not None:
        selector_json["rationale"] = selector.rationale
    return selector_json


def _span_to_json(span: EvalSourceSpanRecord) -> dict[str, object]:
    """Return one JSON-safe source span object."""
    return {
        "start_line": span.start_line,
        "start_column": span.start_column,
        "end_line": span.end_line,
        "end_column": span.end_column,
    }


def _metrics_to_json(metrics: EvalRunMetricRecord) -> dict[str, object]:
    """Return one JSON-safe metric object."""
    return {
        "provider_name": metrics.provider_name,
        "task_id": metrics.task_id,
        "budget": metrics.budget,
        "budget_compliant": metrics.budget_compliant,
        "edit_coverage": metrics.edit_coverage,
        "support_coverage": metrics.support_coverage,
        "representation_adequacy": metrics.representation_adequacy,
        "uncertainty_honesty": metrics.uncertainty_honesty,
        "credited_relevant_tokens": metrics.credited_relevant_tokens,
        "noise_tokens": metrics.noise_tokens,
        "noise_ratio": metrics.noise_ratio,
        "noise_efficiency": metrics.noise_efficiency,
        "aggregate_score": metrics.aggregate_score,
        "total_expected_edit_selectors": metrics.total_expected_edit_selectors,
        "adequate_edit_selectors": metrics.adequate_edit_selectors,
        "total_expected_support_selectors": metrics.total_expected_support_selectors,
        "adequate_support_selectors": metrics.adequate_support_selectors,
        "total_expected_uncertainty_selectors": (
            metrics.total_expected_uncertainty_selectors
        ),
        "represented_expected_selector_count": (
            metrics.represented_expected_selector_count
        ),
        "too_shallow_selector_ids": list(metrics.too_shallow_selector_ids),
        "omitted_expected_uncertainty_ids": list(
            metrics.omitted_expected_uncertainty_ids
        ),
        "selected_matched_selector_ids": list(metrics.selected_matched_selector_ids),
    }
