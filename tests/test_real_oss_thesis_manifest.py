"""Internal real-OSS thesis task manifest contract tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

import context_ir
import context_ir.real_oss_thesis_manifest as real_oss_manifest

_SHA_A = "a" * 40
_SHA_B = "b" * 40


def _line_range(start_line: int = 10, end_line: int = 12) -> dict[str, int]:
    """Return one JSON-safe line range."""
    return {"start_line": start_line, "end_line": end_line}


def _changed_path(
    path: str = "src/pkg/module.py",
    ranges: tuple[dict[str, int], ...] | None = None,
) -> dict[str, object]:
    """Return one JSON-safe changed Python path."""
    return {
        "base_line_ranges": list(ranges if ranges is not None else (_line_range(),)),
        "path": path,
    }


def _leakage_flags(
    *,
    explicit_file_path: bool = False,
    explicit_symbol_name: bool = False,
    stack_trace: bool = False,
    direct_line_number: bool = False,
    patch_like_code_block: bool = False,
) -> dict[str, bool]:
    """Return JSON-safe query leakage flags."""
    return {
        "direct_line_number": direct_line_number,
        "explicit_file_path": explicit_file_path,
        "explicit_symbol_name": explicit_symbol_name,
        "patch_like_code_block": patch_like_code_block,
        "stack_trace": stack_trace,
    }


def _candidate_payload(
    repository_slug: str,
    pr_number: int,
    *,
    changed_python_paths: tuple[dict[str, object], ...] | None = None,
    exclusion_reasons: tuple[str, ...] = (),
    pr_body: str = "Fixes behavior without showing diffs.",
    linked_issue_title: str = "Related issue title",
    linked_issue_body: str = "Related issue body",
    query_leakage_flags: dict[str, bool] | None = None,
) -> dict[str, object]:
    """Return one pre-collected candidate JSON payload."""
    return {
        "base_sha": _SHA_A,
        "changed_python_paths": list(
            changed_python_paths
            if changed_python_paths is not None
            else (_changed_path(f"src/{repository_slug.split('/')[-1]}/feature.py"),)
        ),
        "exclusion_reasons": list(exclusion_reasons),
        "head_sha": _SHA_B,
        "linked_issue_body": linked_issue_body,
        "linked_issue_title": linked_issue_title,
        "pr_body": pr_body,
        "pr_number": pr_number,
        "pr_title": f"Fix issue {pr_number}",
        "query_leakage_flags": (
            query_leakage_flags if query_leakage_flags is not None else _leakage_flags()
        ),
        "repository_slug": repository_slug,
        "repository_url": f"https://github.com/{repository_slug}",
    }


def _candidate_record(
    repository_slug: str,
    pr_number: int,
    *,
    exclusion_reasons: tuple[str, ...] = (),
) -> real_oss_manifest.RealOssCandidateRecord:
    """Return one typed candidate record."""
    return real_oss_manifest.RealOssCandidateRecord(
        repository_slug=repository_slug,
        repository_url=f"https://github.com/{repository_slug}",
        pr_number=pr_number,
        base_sha=_SHA_A,
        head_sha=_SHA_B,
        pr_title=f"Fix issue {pr_number}",
        pr_body="Fixes behavior without showing diffs.",
        linked_issue_title="Related issue title",
        linked_issue_body="Related issue body",
        changed_python_paths=(
            real_oss_manifest.RealOssChangedPythonPath(
                path=f"src/{repository_slug.split('/')[-1]}/feature.py",
                base_line_ranges=(real_oss_manifest.RealOssLineRange(10, 12),),
            ),
        ),
        query_leakage_flags=real_oss_manifest.RealOssQueryLeakageFlags(),
        exclusion_reasons=exclusion_reasons,
    )


def _candidate_records_for_repositories(
    repository_slugs: tuple[str, ...],
    *,
    candidate_count: int,
) -> tuple[real_oss_manifest.RealOssCandidateRecord, ...]:
    """Return eligible typed candidates for each repository slug."""
    records: list[real_oss_manifest.RealOssCandidateRecord] = []
    for repository_slug in repository_slugs:
        for pr_number in range(1, candidate_count + 1):
            records.append(_candidate_record(repository_slug, pr_number))
    return tuple(records)


def _frozen_candidate_records(
    *,
    candidate_count: int,
) -> tuple[real_oss_manifest.RealOssCandidateRecord, ...]:
    """Return eligible typed candidates for the full frozen repository set."""
    return _candidate_records_for_repositories(
        real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES,
        candidate_count=candidate_count,
    )


def test_load_candidate_records_rejects_unknown_fields(tmp_path: Path) -> None:
    """Candidate loading is strict and rejects unregistered schema fields."""
    payload = {
        "candidate_records": [
            {
                **_candidate_payload("pallets/flask", 1),
                "provider_output_hint": "src/app.py",
            }
        ],
        "experiment_version": real_oss_manifest.REAL_OSS_THESIS_EXPERIMENT_VERSION,
    }
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(real_oss_manifest.RealOssThesisManifestError, match="unknown"):
        real_oss_manifest.load_real_oss_candidate_records(candidate_path)


def test_build_manifest_selects_deterministic_precollected_candidates() -> None:
    """Selection is seed-stable, repo-ordered, and independent of input order."""
    records = _frozen_candidate_records(candidate_count=15)

    first_manifest = real_oss_manifest.build_real_oss_task_manifest(records)
    second_manifest = real_oss_manifest.build_real_oss_task_manifest(
        tuple(reversed(records)),
    )
    expected_prs_by_repo = {
        "pallets/flask": (1, 3, 4, 7, 10, 11, 12, 13, 14, 15),
        "encode/httpx": (3, 5, 6, 7, 8, 9, 10, 12, 14, 15),
        "psf/black": (1, 2, 3, 4, 10, 11, 12, 13, 14, 15),
        "scrapy/scrapy": (2, 3, 4, 5, 6, 10, 11, 13, 14, 15),
        "python-poetry/poetry": (1, 3, 5, 6, 7, 8, 9, 11, 12, 13),
    }
    expected_selection = tuple(
        (repository_slug, pr_number)
        for repository_slug in real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES
        for pr_number in expected_prs_by_repo[repository_slug]
    )

    assert first_manifest == second_manifest
    assert first_manifest.experiment_version == "real_oss_thesis_v1"
    assert (
        first_manifest.selection_seed
        == real_oss_manifest.REAL_OSS_THESIS_SELECTION_SEED
    )
    assert (
        first_manifest.tasks_per_repository
        == real_oss_manifest.REAL_OSS_THESIS_TASKS_PER_REPOSITORY
    )
    assert (
        first_manifest.repository_slugs
        == real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES
    )
    assert first_manifest.provider_names == real_oss_manifest.REAL_OSS_THESIS_PROVIDERS
    assert first_manifest.budgets == real_oss_manifest.REAL_OSS_THESIS_BUDGETS
    assert len(first_manifest.selected_tasks) == 50
    assert (
        tuple(
            (task.repository_slug, task.pr_number)
            for task in first_manifest.selected_tasks
        )
        == expected_selection
    )
    assert first_manifest.selected_tasks[0].task_id == (
        "real_oss_thesis_v1:pallets__flask:pr-1"
    )


def test_build_manifest_rejects_non_frozen_plan_overrides() -> None:
    """Manifest construction cannot override the frozen pre-registration plan."""
    records = _frozen_candidate_records(candidate_count=15)
    reordered_repositories = (
        real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES[1:]
        + real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES[:1]
    )

    with pytest.raises(
        real_oss_manifest.RealOssThesisManifestError,
        match="selection_seed",
    ):
        real_oss_manifest.build_real_oss_task_manifest(
            records,
            selection_seed=20260608,
        )
    with pytest.raises(
        real_oss_manifest.RealOssThesisManifestError,
        match="tasks_per_repository",
    ):
        real_oss_manifest.build_real_oss_task_manifest(
            records,
            tasks_per_repository=9,
        )
    with pytest.raises(
        real_oss_manifest.RealOssThesisManifestError,
        match="repository_slugs",
    ):
        real_oss_manifest.build_real_oss_task_manifest(
            records,
            repository_slugs=reordered_repositories,
        )


def test_manifest_rejects_non_frozen_plan_fields() -> None:
    """Typed manifests reject direct construction drift from the frozen plan."""
    manifest = real_oss_manifest.build_real_oss_task_manifest(
        _frozen_candidate_records(candidate_count=10),
    )
    reordered_repositories = (
        manifest.repository_slugs[1:] + manifest.repository_slugs[:1]
    )
    incomplete_repositories = manifest.repository_slugs[:-1]

    with pytest.raises(ValueError, match="selection_seed"):
        replace(manifest, selection_seed=20260608)
    with pytest.raises(ValueError, match="tasks_per_repository"):
        replace(manifest, tasks_per_repository=9)
    with pytest.raises(ValueError, match="repository_slugs"):
        replace(manifest, repository_slugs=reordered_repositories)
    with pytest.raises(ValueError, match="repository_slugs"):
        replace(manifest, repository_slugs=incomplete_repositories)


def test_build_manifest_ignores_excluded_candidates() -> None:
    """Pre-collected excluded candidates cannot enter deterministic sampling."""
    records = (
        real_oss_manifest.RealOssCandidateRecord(
            repository_slug="pallets/flask",
            repository_url="https://github.com/pallets/flask",
            pr_number=1,
            base_sha=_SHA_A,
            head_sha=_SHA_B,
            pr_title="Docs-only change",
            pr_body="No Python retrieval target.",
            linked_issue_title="",
            linked_issue_body="",
            changed_python_paths=(),
            query_leakage_flags=real_oss_manifest.RealOssQueryLeakageFlags(),
            exclusion_reasons=("no base-side Python ranges",),
        ),
        *(_candidate_record("pallets/flask", pr_number) for pr_number in range(2, 12)),
        *_candidate_records_for_repositories(
            real_oss_manifest.REAL_OSS_THESIS_REPOSITORIES[1:],
            candidate_count=10,
        ),
    )

    manifest = real_oss_manifest.build_real_oss_task_manifest(records)

    assert tuple(
        task.pr_number
        for task in manifest.selected_tasks
        if task.repository_slug == "pallets/flask"
    ) == (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)


def test_build_manifest_rejects_insufficient_eligible_candidates() -> None:
    """Every frozen repository in scope must have enough eligible candidates."""
    records = tuple(
        record
        for record in _frozen_candidate_records(candidate_count=10)
        if not (record.repository_slug == "pallets/flask" and record.pr_number == 10)
    )

    with pytest.raises(
        real_oss_manifest.RealOssThesisManifestError,
        match="only 9 eligible",
    ):
        real_oss_manifest.build_real_oss_task_manifest(records)


def test_candidate_records_enforce_mechanical_size_thresholds(
    tmp_path: Path,
) -> None:
    """Pre-registration size thresholds are enforced before manifest selection."""
    oversized_range = _line_range(1, 81)
    payload = {
        "candidate_records": [
            _candidate_payload(
                "pallets/flask",
                1,
                changed_python_paths=(
                    _changed_path("src/flask/feature.py", ranges=(oversized_range,)),
                ),
            )
        ],
        "experiment_version": real_oss_manifest.REAL_OSS_THESIS_EXPERIMENT_VERSION,
    }
    candidate_path = tmp_path / "candidates.json"
    candidate_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="single-file changed line threshold"):
        real_oss_manifest.load_real_oss_candidate_records(candidate_path)


def test_manifest_json_round_trips_without_provider_outputs(tmp_path: Path) -> None:
    """Manifest serialization records only task facts, not retrieval results."""
    manifest = real_oss_manifest.build_real_oss_task_manifest(
        _frozen_candidate_records(candidate_count=10),
    )
    output_path = tmp_path / "real_oss" / "task_manifest.json"

    written_path = real_oss_manifest.write_real_oss_task_manifest_json(
        manifest,
        output_path,
    )
    payload = real_oss_manifest.real_oss_task_manifest_to_json(manifest)

    assert written_path == output_path
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert set(payload) == {
        "budgets",
        "experiment_version",
        "provider_names",
        "repository_slugs",
        "selected_tasks",
        "selection_seed",
        "task_count",
        "tasks_per_repository",
    }
    assert payload["task_count"] == 50
    assert "provider_outputs" not in payload
    assert "scores" not in payload
    assert "embedding_vectors" not in payload
    assert "github_api_responses" not in payload


def test_manifest_rejects_inconsistent_task_counts() -> None:
    """Manifest construction rejects task-count drift."""
    manifest = real_oss_manifest.build_real_oss_task_manifest(
        _frozen_candidate_records(candidate_count=10),
    )

    with pytest.raises(ValueError, match="selected task count"):
        replace(manifest, selected_tasks=manifest.selected_tasks[:1])


def test_real_oss_manifest_contracts_remain_internal() -> None:
    """Real-OSS thesis manifest helpers are not package-root public API."""
    forbidden_names = set(real_oss_manifest.__all__)

    assert forbidden_names.isdisjoint(set(context_ir.__all__))
    for forbidden_name in forbidden_names:
        assert not hasattr(context_ir, forbidden_name)
    assert not hasattr(real_oss_manifest, "run_real_oss_experiment")
    assert not hasattr(real_oss_manifest, "fetch_github_pull_requests")
    assert not hasattr(real_oss_manifest, "run_embedding_provider")
    assert not hasattr(real_oss_manifest, "score_real_oss_results")
