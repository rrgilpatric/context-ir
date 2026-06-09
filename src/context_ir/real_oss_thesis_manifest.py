"""Internal real-OSS thesis task manifest contracts."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

REAL_OSS_THESIS_EXPERIMENT_VERSION = "real_oss_thesis_v1"
REAL_OSS_THESIS_SELECTION_SEED = 20260607
REAL_OSS_THESIS_TASKS_PER_REPOSITORY = 10
REAL_OSS_THESIS_REPOSITORIES = (
    "pallets/flask",
    "encode/httpx",
    "psf/black",
    "scrapy/scrapy",
    "python-poetry/poetry",
)
REAL_OSS_THESIS_PROVIDERS = (
    "context_ir_static",
    "bm25_chunks",
    "embedding_chunks",
)
REAL_OSS_THESIS_BUDGETS = (2000, 4000, 8000)
REAL_OSS_THESIS_MAX_CHANGED_PY_FILES = 5
REAL_OSS_THESIS_MAX_TOTAL_BASE_CHANGED_LINES = 200
REAL_OSS_THESIS_MAX_SINGLE_FILE_BASE_CHANGED_LINES = 80

_CANDIDATE_ROOT_FIELDS = frozenset({"experiment_version", "candidate_records"})
_CANDIDATE_RECORD_FIELDS = frozenset(
    {
        "repository_slug",
        "repository_url",
        "pr_number",
        "base_sha",
        "head_sha",
        "pr_title",
        "pr_body",
        "linked_issue_title",
        "linked_issue_body",
        "changed_python_paths",
        "query_leakage_flags",
        "exclusion_reasons",
    }
)
_CHANGED_PATH_FIELDS = frozenset({"path", "base_line_ranges"})
_LINE_RANGE_FIELDS = frozenset({"start_line", "end_line"})
_LEAKAGE_FLAG_FIELDS = frozenset(
    {
        "explicit_file_path",
        "explicit_symbol_name",
        "stack_trace",
        "direct_line_number",
        "patch_like_code_block",
    }
)
_EXCLUDED_PATH_PARTS = frozenset(
    {
        ".git",
        ".hg",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "site-packages",
        "vendor",
        "vendored",
    }
)
_HEX_DIGITS = frozenset("0123456789abcdef")


class RealOssThesisManifestError(ValueError):
    """Raised when real-OSS thesis manifest input violates the frozen contract."""


@dataclass(frozen=True)
class RealOssLineRange:
    """Inclusive base-side changed line range for one Python file."""

    start_line: int
    end_line: int

    def __post_init__(self) -> None:
        """Reject malformed or empty line ranges."""
        if self.start_line <= 0:
            raise ValueError("start_line must be positive")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")

    @property
    def line_count(self) -> int:
        """Return the inclusive line count covered by this range."""
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class RealOssChangedPythonPath:
    """One changed Python path plus base-side changed ranges."""

    path: str
    base_line_ranges: tuple[RealOssLineRange, ...]

    def __post_init__(self) -> None:
        """Reject non-Python, generated, vendored, or targetless paths."""
        if not self.path:
            raise ValueError("changed path must be non-empty")
        posix_path = PurePosixPath(self.path)
        if posix_path.is_absolute():
            raise ValueError("changed path must be repo-relative")
        if ".." in posix_path.parts:
            raise ValueError("changed path must not contain parent traversal")
        if not self.path.endswith(".py"):
            raise ValueError("changed path must end with .py")
        if _EXCLUDED_PATH_PARTS & frozenset(posix_path.parts):
            raise ValueError("changed path must not be generated, vendored, or cached")
        if not self.base_line_ranges:
            raise ValueError("changed path must include base-side line ranges")

    @property
    def base_changed_line_count(self) -> int:
        """Return base-side changed lines for this path."""
        return sum(line_range.line_count for line_range in self.base_line_ranges)


@dataclass(frozen=True)
class RealOssQueryLeakageFlags:
    """Pre-scoring query leakage flags for one candidate PR."""

    explicit_file_path: bool = False
    explicit_symbol_name: bool = False
    stack_trace: bool = False
    direct_line_number: bool = False
    patch_like_code_block: bool = False


@dataclass(frozen=True)
class RealOssCandidateRecord:
    """Pre-collected candidate PR metadata independent of Context IR output."""

    repository_slug: str
    repository_url: str
    pr_number: int
    base_sha: str
    head_sha: str
    pr_title: str
    pr_body: str
    linked_issue_title: str
    linked_issue_body: str
    changed_python_paths: tuple[RealOssChangedPythonPath, ...]
    query_leakage_flags: RealOssQueryLeakageFlags
    exclusion_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject malformed candidate metadata before deterministic selection."""
        if self.repository_slug not in REAL_OSS_THESIS_REPOSITORIES:
            raise ValueError("repository_slug is not in the frozen repository set")
        expected_url = f"https://github.com/{self.repository_slug}"
        if self.repository_url != expected_url:
            raise ValueError("repository_url must match the frozen GitHub slug")
        if self.pr_number <= 0:
            raise ValueError("pr_number must be positive")
        _validate_sha(self.base_sha, field_name="base_sha")
        _validate_sha(self.head_sha, field_name="head_sha")
        if not self.pr_title.strip():
            raise ValueError("pr_title must be non-empty")
        if not self.changed_python_paths and not self.exclusion_reasons:
            raise ValueError("candidate must include changed Python paths")
        if not self.exclusion_reasons:
            _validate_mechanical_thresholds(self)
        if any(not reason.strip() for reason in self.exclusion_reasons):
            raise ValueError("exclusion_reasons must not contain blank text")

    @property
    def is_eligible(self) -> bool:
        """Return whether this pre-collected candidate can enter sampling."""
        return not self.exclusion_reasons

    @property
    def total_base_changed_lines(self) -> int:
        """Return total base-side changed lines across all changed Python paths."""
        return sum(path.base_changed_line_count for path in self.changed_python_paths)


@dataclass(frozen=True)
class RealOssSelectedTask:
    """One selected real-OSS thesis task with git-fact oracle fields."""

    task_id: str
    repository_slug: str
    repository_url: str
    pr_number: int
    base_sha: str
    head_sha: str
    query: str
    changed_python_paths: tuple[RealOssChangedPythonPath, ...]
    query_leakage_flags: RealOssQueryLeakageFlags

    def __post_init__(self) -> None:
        """Reject malformed selected task records."""
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if not self.query.strip():
            raise ValueError("query must be non-empty")
        if not self.changed_python_paths:
            raise ValueError("selected task must include oracle ranges")


@dataclass(frozen=True)
class RealOssTaskManifest:
    """Frozen task manifest for the real-OSS thesis experiment."""

    experiment_version: str
    selection_seed: int
    tasks_per_repository: int
    repository_slugs: tuple[str, ...]
    provider_names: tuple[str, ...]
    budgets: tuple[int, ...]
    selected_tasks: tuple[RealOssSelectedTask, ...]

    def __post_init__(self) -> None:
        """Reject incomplete or internally inconsistent manifests."""
        if self.experiment_version != REAL_OSS_THESIS_EXPERIMENT_VERSION:
            raise ValueError("experiment_version is unsupported")
        _validate_frozen_manifest_plan(
            repository_slugs=self.repository_slugs,
            tasks_per_repository=self.tasks_per_repository,
            selection_seed=self.selection_seed,
            error_type=ValueError,
        )
        if not self.provider_names:
            raise ValueError("provider_names must be non-empty")
        if not self.budgets:
            raise ValueError("budgets must be non-empty")
        if any(budget <= 0 for budget in self.budgets):
            raise ValueError("budgets must contain only positive integers")
        if self.provider_names != REAL_OSS_THESIS_PROVIDERS:
            raise ValueError("provider_names must match the frozen provider set")
        if self.budgets != REAL_OSS_THESIS_BUDGETS:
            raise ValueError("budgets must match the frozen budget set")
        expected_task_count = self.tasks_per_repository * len(self.repository_slugs)
        if len(self.selected_tasks) != expected_task_count:
            raise ValueError("selected task count does not match repository plan")

        seen_task_ids: set[str] = set()
        seen_repo_prs: set[tuple[str, int]] = set()
        counts_by_repo = {
            repository_slug: 0 for repository_slug in self.repository_slugs
        }
        for task in self.selected_tasks:
            if task.task_id in seen_task_ids:
                raise ValueError(f"duplicate task_id '{task.task_id}'")
            seen_task_ids.add(task.task_id)
            repo_pr_key = (task.repository_slug, task.pr_number)
            if repo_pr_key in seen_repo_prs:
                raise ValueError("duplicate repository/pr selected task")
            seen_repo_prs.add(repo_pr_key)
            if task.repository_slug not in counts_by_repo:
                raise ValueError("selected task repository is outside manifest scope")
            counts_by_repo[task.repository_slug] += 1

        for repository_slug, task_count in counts_by_repo.items():
            if task_count != self.tasks_per_repository:
                raise ValueError(
                    f"repository '{repository_slug}' has {task_count} selected tasks"
                )


def load_real_oss_candidate_records(
    path: Path | str,
) -> tuple[RealOssCandidateRecord, ...]:
    """Load pre-collected candidate records from a strict JSON artifact."""
    source_path = Path(path)
    try:
        raw: object = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RealOssThesisManifestError(
            f"invalid candidate JSON in {source_path}: {error}"
        ) from error

    record = _expect_object(raw, path="$")
    _validate_allowed_fields(record, _CANDIDATE_ROOT_FIELDS, path="$")
    experiment_version = _required_string(record, "experiment_version", path="$")
    if experiment_version != REAL_OSS_THESIS_EXPERIMENT_VERSION:
        raise RealOssThesisManifestError("candidate experiment_version is unsupported")
    candidates_raw = _required_list(record, "candidate_records", path="$")
    return tuple(
        _parse_candidate_record(raw_candidate, path=f"$.candidate_records[{index}]")
        for index, raw_candidate in enumerate(candidates_raw)
    )


def build_real_oss_task_manifest(
    candidate_records: tuple[RealOssCandidateRecord, ...],
    *,
    repository_slugs: tuple[str, ...] = REAL_OSS_THESIS_REPOSITORIES,
    tasks_per_repository: int = REAL_OSS_THESIS_TASKS_PER_REPOSITORY,
    selection_seed: int = REAL_OSS_THESIS_SELECTION_SEED,
) -> RealOssTaskManifest:
    """Select a deterministic task manifest from pre-collected candidates."""
    _validate_frozen_manifest_plan(
        repository_slugs=repository_slugs,
        tasks_per_repository=tasks_per_repository,
        selection_seed=selection_seed,
        error_type=RealOssThesisManifestError,
    )
    _reject_duplicate_candidates(candidate_records)

    eligible_by_repo: dict[str, list[RealOssCandidateRecord]] = {
        repository_slug: [] for repository_slug in repository_slugs
    }
    for candidate in candidate_records:
        if (
            candidate.repository_slug not in eligible_by_repo
            or not candidate.is_eligible
        ):
            continue
        _validate_mechanical_thresholds(candidate)
        eligible_by_repo[candidate.repository_slug].append(candidate)

    rng = random.Random(selection_seed)
    selected_tasks: list[RealOssSelectedTask] = []
    for repository_slug in repository_slugs:
        eligible_candidates = sorted(
            eligible_by_repo[repository_slug],
            key=lambda candidate: candidate.pr_number,
        )
        if len(eligible_candidates) < tasks_per_repository:
            raise RealOssThesisManifestError(
                f"repository '{repository_slug}' has only "
                f"{len(eligible_candidates)} eligible candidates"
            )
        sampled_candidates = sorted(
            rng.sample(eligible_candidates, tasks_per_repository),
            key=lambda candidate: candidate.pr_number,
        )
        selected_tasks.extend(
            _selected_task_from_candidate(candidate) for candidate in sampled_candidates
        )

    return RealOssTaskManifest(
        experiment_version=REAL_OSS_THESIS_EXPERIMENT_VERSION,
        selection_seed=selection_seed,
        tasks_per_repository=tasks_per_repository,
        repository_slugs=repository_slugs,
        provider_names=REAL_OSS_THESIS_PROVIDERS,
        budgets=REAL_OSS_THESIS_BUDGETS,
        selected_tasks=tuple(selected_tasks),
    )


def real_oss_task_manifest_to_json(
    manifest: RealOssTaskManifest,
) -> dict[str, object]:
    """Serialize one real-OSS task manifest into deterministic JSON-safe data."""
    return {
        "budgets": list(manifest.budgets),
        "experiment_version": manifest.experiment_version,
        "provider_names": list(manifest.provider_names),
        "repository_slugs": list(manifest.repository_slugs),
        "selected_tasks": [
            _selected_task_to_json(task) for task in manifest.selected_tasks
        ],
        "selection_seed": manifest.selection_seed,
        "task_count": len(manifest.selected_tasks),
        "tasks_per_repository": manifest.tasks_per_repository,
    }


def write_real_oss_task_manifest_json(
    manifest: RealOssTaskManifest,
    output_path: Path | str,
) -> Path:
    """Write a real-OSS task manifest JSON artifact to disk."""
    destination_path = Path(output_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text(
        json.dumps(
            real_oss_task_manifest_to_json(manifest),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return destination_path


def _selected_task_from_candidate(
    candidate: RealOssCandidateRecord,
) -> RealOssSelectedTask:
    """Return one manifest task from a selected candidate record."""
    return RealOssSelectedTask(
        task_id=_task_id(candidate.repository_slug, candidate.pr_number),
        repository_slug=candidate.repository_slug,
        repository_url=candidate.repository_url,
        pr_number=candidate.pr_number,
        base_sha=candidate.base_sha,
        head_sha=candidate.head_sha,
        query=_query_from_candidate(candidate),
        changed_python_paths=candidate.changed_python_paths,
        query_leakage_flags=candidate.query_leakage_flags,
    )


def _query_from_candidate(candidate: RealOssCandidateRecord) -> str:
    """Build the deterministic query text from pre-collected PR/issue text."""
    parts = (
        candidate.pr_title.strip(),
        candidate.pr_body.strip(),
        candidate.linked_issue_title.strip(),
        candidate.linked_issue_body.strip(),
    )
    return "\n\n".join(part for part in parts if part)


def _task_id(repository_slug: str, pr_number: int) -> str:
    """Return a stable manifest-local task identifier."""
    normalized_slug = repository_slug.replace("/", "__")
    return f"{REAL_OSS_THESIS_EXPERIMENT_VERSION}:{normalized_slug}:pr-{pr_number}"


def _validate_mechanical_thresholds(candidate: RealOssCandidateRecord) -> None:
    """Enforce frozen mechanical PR-size thresholds from pre-registration."""
    if len(candidate.changed_python_paths) > REAL_OSS_THESIS_MAX_CHANGED_PY_FILES:
        raise ValueError("candidate exceeds changed Python file threshold")
    if (
        candidate.total_base_changed_lines
        > REAL_OSS_THESIS_MAX_TOTAL_BASE_CHANGED_LINES
    ):
        raise ValueError("candidate exceeds total base-side changed line threshold")
    for changed_path in candidate.changed_python_paths:
        if (
            changed_path.base_changed_line_count
            > REAL_OSS_THESIS_MAX_SINGLE_FILE_BASE_CHANGED_LINES
        ):
            raise ValueError("candidate exceeds single-file changed line threshold")


def _reject_duplicate_candidates(
    candidate_records: tuple[RealOssCandidateRecord, ...],
) -> None:
    """Reject duplicate repository/PR candidate records."""
    seen: set[tuple[str, int]] = set()
    for candidate in candidate_records:
        key = (candidate.repository_slug, candidate.pr_number)
        if key in seen:
            raise RealOssThesisManifestError("duplicate repository/pr candidate")
        seen.add(key)


def _validate_frozen_manifest_plan(
    *,
    repository_slugs: tuple[str, ...],
    tasks_per_repository: int,
    selection_seed: int,
    error_type: type[ValueError],
) -> None:
    """Reject manifest plan drift from the frozen pre-registration contract."""
    if selection_seed != REAL_OSS_THESIS_SELECTION_SEED:
        raise error_type("selection_seed must match the frozen v1 seed")
    if tasks_per_repository != REAL_OSS_THESIS_TASKS_PER_REPOSITORY:
        raise error_type("tasks_per_repository must match the frozen v1 task count")
    if repository_slugs != REAL_OSS_THESIS_REPOSITORIES:
        raise error_type(
            "repository_slugs must match the frozen v1 repository set and order"
        )


def _selected_task_to_json(task: RealOssSelectedTask) -> dict[str, object]:
    """Return JSON-safe content for one selected task."""
    return {
        "base_sha": task.base_sha,
        "changed_python_paths": [
            _changed_path_to_json(changed_path)
            for changed_path in task.changed_python_paths
        ],
        "head_sha": task.head_sha,
        "pr_number": task.pr_number,
        "query": task.query,
        "query_leakage_flags": _leakage_flags_to_json(task.query_leakage_flags),
        "repository_slug": task.repository_slug,
        "repository_url": task.repository_url,
        "task_id": task.task_id,
    }


def _changed_path_to_json(changed_path: RealOssChangedPythonPath) -> dict[str, object]:
    """Return JSON-safe content for one changed Python path."""
    return {
        "base_line_ranges": [
            _line_range_to_json(line_range)
            for line_range in changed_path.base_line_ranges
        ],
        "path": changed_path.path,
    }


def _line_range_to_json(line_range: RealOssLineRange) -> dict[str, int]:
    """Return JSON-safe content for one line range."""
    return {
        "end_line": line_range.end_line,
        "start_line": line_range.start_line,
    }


def _leakage_flags_to_json(flags: RealOssQueryLeakageFlags) -> dict[str, bool]:
    """Return JSON-safe content for query leakage flags."""
    return {
        "direct_line_number": flags.direct_line_number,
        "explicit_file_path": flags.explicit_file_path,
        "explicit_symbol_name": flags.explicit_symbol_name,
        "patch_like_code_block": flags.patch_like_code_block,
        "stack_trace": flags.stack_trace,
    }


def _parse_candidate_record(
    raw: object,
    *,
    path: str,
) -> RealOssCandidateRecord:
    """Parse one strict candidate record from JSON content."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(record, _CANDIDATE_RECORD_FIELDS, path=path)
    changed_paths_raw = _required_list(record, "changed_python_paths", path=path)
    exclusion_reasons_raw = _required_list(record, "exclusion_reasons", path=path)
    return RealOssCandidateRecord(
        repository_slug=_required_string(record, "repository_slug", path=path),
        repository_url=_required_string(record, "repository_url", path=path),
        pr_number=_required_int(record, "pr_number", path=path),
        base_sha=_required_string(record, "base_sha", path=path),
        head_sha=_required_string(record, "head_sha", path=path),
        pr_title=_required_string(record, "pr_title", path=path),
        pr_body=_required_string(record, "pr_body", path=path),
        linked_issue_title=_required_string(
            record,
            "linked_issue_title",
            path=path,
        ),
        linked_issue_body=_required_string(record, "linked_issue_body", path=path),
        changed_python_paths=tuple(
            _parse_changed_path(
                changed_path_raw,
                path=f"{path}.changed_python_paths[{index}]",
            )
            for index, changed_path_raw in enumerate(changed_paths_raw)
        ),
        query_leakage_flags=_parse_leakage_flags(
            _required_object(record, "query_leakage_flags", path=path),
            path=f"{path}.query_leakage_flags",
        ),
        exclusion_reasons=tuple(
            _parse_text(
                reason_raw,
                path=f"{path}.exclusion_reasons[{index}]",
            )
            for index, reason_raw in enumerate(exclusion_reasons_raw)
        ),
    )


def _parse_changed_path(
    raw: object,
    *,
    path: str,
) -> RealOssChangedPythonPath:
    """Parse one changed Python path from strict JSON content."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(record, _CHANGED_PATH_FIELDS, path=path)
    ranges_raw = _required_list(record, "base_line_ranges", path=path)
    return RealOssChangedPythonPath(
        path=_required_string(record, "path", path=path),
        base_line_ranges=tuple(
            _parse_line_range(line_range_raw, path=f"{path}.base_line_ranges[{index}]")
            for index, line_range_raw in enumerate(ranges_raw)
        ),
    )


def _parse_line_range(raw: object, *, path: str) -> RealOssLineRange:
    """Parse one line range from strict JSON content."""
    record = _expect_object(raw, path=path)
    _validate_allowed_fields(record, _LINE_RANGE_FIELDS, path=path)
    return RealOssLineRange(
        start_line=_required_int(record, "start_line", path=path),
        end_line=_required_int(record, "end_line", path=path),
    )


def _parse_leakage_flags(
    record: dict[str, object],
    *,
    path: str,
) -> RealOssQueryLeakageFlags:
    """Parse query leakage flags from strict JSON content."""
    _validate_allowed_fields(record, _LEAKAGE_FLAG_FIELDS, path=path)
    return RealOssQueryLeakageFlags(
        explicit_file_path=_required_bool(record, "explicit_file_path", path=path),
        explicit_symbol_name=_required_bool(record, "explicit_symbol_name", path=path),
        stack_trace=_required_bool(record, "stack_trace", path=path),
        direct_line_number=_required_bool(record, "direct_line_number", path=path),
        patch_like_code_block=_required_bool(
            record,
            "patch_like_code_block",
            path=path,
        ),
    )


def _expect_object(raw: object, *, path: str) -> dict[str, object]:
    """Return a JSON object or raise a schema error."""
    if not isinstance(raw, dict):
        raise RealOssThesisManifestError(f"{path} must be an object")
    return cast(dict[str, object], raw)


def _required_object(
    record: dict[str, object],
    field_name: str,
    *,
    path: str,
) -> dict[str, object]:
    """Return a required object field."""
    if field_name not in record:
        raise RealOssThesisManifestError(f"{path}.{field_name} is required")
    return _expect_object(record[field_name], path=f"{path}.{field_name}")


def _required_list(
    record: dict[str, object],
    field_name: str,
    *,
    path: str,
) -> list[object]:
    """Return a required list field."""
    if field_name not in record:
        raise RealOssThesisManifestError(f"{path}.{field_name} is required")
    value = record[field_name]
    if not isinstance(value, list):
        raise RealOssThesisManifestError(f"{path}.{field_name} must be a list")
    return cast(list[object], value)


def _required_string(
    record: dict[str, object],
    field_name: str,
    *,
    path: str,
) -> str:
    """Return a required string field."""
    if field_name not in record:
        raise RealOssThesisManifestError(f"{path}.{field_name} is required")
    return _parse_text(record[field_name], path=f"{path}.{field_name}")


def _required_int(
    record: dict[str, object],
    field_name: str,
    *,
    path: str,
) -> int:
    """Return a required integer field."""
    if field_name not in record:
        raise RealOssThesisManifestError(f"{path}.{field_name} is required")
    value = record[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RealOssThesisManifestError(f"{path}.{field_name} must be an integer")
    return value


def _required_bool(
    record: dict[str, object],
    field_name: str,
    *,
    path: str,
) -> bool:
    """Return a required boolean field."""
    if field_name not in record:
        raise RealOssThesisManifestError(f"{path}.{field_name} is required")
    value = record[field_name]
    if not isinstance(value, bool):
        raise RealOssThesisManifestError(f"{path}.{field_name} must be boolean")
    return value


def _parse_text(raw: object, *, path: str) -> str:
    """Return a string value from JSON content."""
    if not isinstance(raw, str):
        raise RealOssThesisManifestError(f"{path} must be a string")
    return raw


def _validate_allowed_fields(
    record: dict[str, object],
    allowed_fields: frozenset[str],
    *,
    path: str,
) -> None:
    """Reject unknown JSON object fields."""
    unknown_fields = sorted(set(record) - allowed_fields)
    if unknown_fields:
        rendered = ", ".join(unknown_fields)
        raise RealOssThesisManifestError(f"{path} has unknown fields: {rendered}")


def _validate_sha(value: str, *, field_name: str) -> None:
    """Validate a full lowercase hexadecimal git SHA."""
    if len(value) != 40 or not frozenset(value) <= _HEX_DIGITS:
        raise ValueError(f"{field_name} must be a 40-character lowercase hex SHA")


__all__ = [
    "REAL_OSS_THESIS_BUDGETS",
    "REAL_OSS_THESIS_EXPERIMENT_VERSION",
    "REAL_OSS_THESIS_MAX_CHANGED_PY_FILES",
    "REAL_OSS_THESIS_MAX_SINGLE_FILE_BASE_CHANGED_LINES",
    "REAL_OSS_THESIS_MAX_TOTAL_BASE_CHANGED_LINES",
    "REAL_OSS_THESIS_PROVIDERS",
    "REAL_OSS_THESIS_REPOSITORIES",
    "REAL_OSS_THESIS_SELECTION_SEED",
    "REAL_OSS_THESIS_TASKS_PER_REPOSITORY",
    "RealOssCandidateRecord",
    "RealOssChangedPythonPath",
    "RealOssLineRange",
    "RealOssQueryLeakageFlags",
    "RealOssSelectedTask",
    "RealOssTaskManifest",
    "RealOssThesisManifestError",
    "build_real_oss_task_manifest",
    "load_real_oss_candidate_records",
    "real_oss_task_manifest_to_json",
    "write_real_oss_task_manifest_json",
]
