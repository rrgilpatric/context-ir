"""Deterministic internal eval context providers and baselines."""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import context_ir.tool_facade as tool_facade
from context_ir.semantic_types import (
    SemanticOptimizationWarning,
    SemanticSelectionRecord,
)

CONTEXT_IR_PROVIDER = "context_ir"
LEXICAL_TOP_K_FILES_PROVIDER = "lexical_top_k_files"
IMPORT_NEIGHBORHOOD_FILES_PROVIDER = "import_neighborhood_files"
FILE_ORDER_FLOOR_PROVIDER = "file_order_floor"
PROVIDER_ALGORITHM_VERSION = "v1"
LEXICAL_MAX_CANDIDATES = 8
IMPORT_SEED_COUNT = 2

_RAW_TOKEN_PATTERN = re.compile(r"[^A-Za-z0-9]+")
_CAMEL_PART_PATTERN = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[0-9]+")


@dataclass(frozen=True)
class EvalProviderRequest:
    """Inputs shared by deterministic eval context providers."""

    repo_root: Path | str
    task_id: str
    query: str
    budget: int

    def __post_init__(self) -> None:
        """Reject invalid task identity and impossible budgets."""
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")


@dataclass(frozen=True)
class EvalProviderConfig:
    """Typed provider configuration recorded with each provider output."""

    max_candidates: int | None = None
    seed_count: int | None = None
    diagnostic_only: bool = False


@dataclass(frozen=True)
class LexicalFileScore:
    """Deterministic lexical score metadata for one repository file."""

    file_path: str
    score: float
    token_count: int


@dataclass(frozen=True)
class EvalSelectedUnit:
    """Structured selected-unit trace metadata preserved for eval scoring."""

    unit_id: str
    detail: str
    token_count: int
    basis: str
    reason: str | None = None
    edit_score: float | None = None
    support_score: float | None = None

    def __post_init__(self) -> None:
        """Reject empty identifiers and impossible selection metadata."""
        if not self.unit_id:
            raise ValueError("unit_id must be non-empty")
        if not self.detail:
            raise ValueError("detail must be non-empty")
        if self.token_count < 0:
            raise ValueError("token_count must be >= 0")
        if not self.basis:
            raise ValueError("basis must be non-empty")
        if self.reason == "":
            raise ValueError("reason must be non-empty when provided")
        if self.edit_score is not None and not 0.0 <= self.edit_score <= 1.0:
            raise ValueError("edit_score must be within [0.0, 1.0]")
        if self.support_score is not None and not 0.0 <= self.support_score <= 1.0:
            raise ValueError("support_score must be within [0.0, 1.0]")


@dataclass(frozen=True)
class EvalProviderWarning:
    """Structured provider warning metadata preserved for eval scoring."""

    code: str
    unit_id: str | None
    message: str

    def __post_init__(self) -> None:
        """Reject empty warning fields."""
        if not self.code:
            raise ValueError("code must be non-empty")
        if self.unit_id == "":
            raise ValueError("unit_id must be non-empty when provided")
        if not self.message:
            raise ValueError("message must be non-empty")


@dataclass(frozen=True)
class EvalProviderMetadata:
    """Structured provider metadata reserved for later eval scoring and reports."""

    diagnostic_only: bool = False
    candidate_files: tuple[str, ...] = ()
    omitted_candidate_files: tuple[str, ...] = ()
    lexical_scores: tuple[LexicalFileScore, ...] = ()
    selected_units: tuple[EvalSelectedUnit, ...] = ()
    warning_details: tuple[EvalProviderWarning, ...] = ()
    unresolved_unit_ids: tuple[str, ...] = ()
    unsupported_unit_ids: tuple[str, ...] = ()
    syntax_diagnostic_ids: tuple[str, ...] = ()
    semantic_diagnostic_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvalProviderResult:
    """Internal deterministic provider output for one eval task request."""

    provider_name: str
    provider_algorithm_version: str
    provider_config: EvalProviderConfig
    task_id: str
    query: str
    budget: int
    document: str
    total_tokens: int
    selected_files: tuple[str, ...]
    omitted_candidate_files: tuple[str, ...]
    selected_unit_ids: tuple[str, ...]
    omitted_unit_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    metadata: EvalProviderMetadata

    def __post_init__(self) -> None:
        """Keep provider outputs budget-honest and internally consistent."""
        if not self.provider_name:
            raise ValueError("provider_name must be non-empty")
        if not self.provider_algorithm_version:
            raise ValueError("provider_algorithm_version must be non-empty")
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if not self.document:
            raise ValueError("document must be non-empty")
        if self.budget < 0:
            raise ValueError("budget must be >= 0")
        if self.total_tokens < 0:
            raise ValueError("total_tokens must be >= 0")
        if self.total_tokens > self.budget:
            raise ValueError("provider output exceeds budget")
        if self.total_tokens != estimate_tokens(self.document):
            raise ValueError("total_tokens must match the provider token estimator")
        if self.omitted_candidate_files != self.metadata.omitted_candidate_files:
            raise ValueError("omitted_candidate_files must mirror metadata")
        if self.provider_name == CONTEXT_IR_PROVIDER:
            if self.selected_unit_ids != tuple(
                unit.unit_id for unit in self.metadata.selected_units
            ):
                raise ValueError(
                    "selected_unit_ids must mirror structured selected-unit metadata"
                )
            if self.warnings != tuple(
                warning.code for warning in self.metadata.warning_details
            ):
                raise ValueError("warnings must mirror structured warning metadata")


@dataclass(frozen=True)
class _BaselineFile:
    """Repository file candidate used by deterministic file baselines."""

    relative_path: str
    text: str
    token_count: int


@dataclass(frozen=True)
class _ScoredBaselineFile:
    """Lexically scored repository file candidate."""

    file: _BaselineFile
    score: float
    content_terms: Counter[str]
    path_terms: tuple[str, ...]


def estimate_tokens(text: str) -> int:
    """Estimate token count using the accepted eval provider heuristic."""
    return max(1, (len(text) + 3) // 4)


def lexical_tokens(text: str) -> tuple[str, ...]:
    """Tokenize text for deterministic lexical baseline scoring."""
    terms: list[str] = []
    for raw_token in _RAW_TOKEN_PATTERN.split(text):
        if not raw_token:
            continue
        terms.append(raw_token.lower())
        terms.extend(part.lower() for part in _CAMEL_PART_PATTERN.findall(raw_token))
    return tuple(term for term in terms if term)


def build_context_ir_provider_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Compile a Context IR provider pack through the accepted tool facade."""
    response = tool_facade.compile_repository_context(
        tool_facade.SemanticContextRequest(
            repo_root=request.repo_root,
            query=request.query,
            budget=request.budget,
            embed_fn=None,
        )
    )
    selected_units = tuple(
        _selected_unit_metadata(record) for record in response.selection_trace
    )
    warning_details = tuple(
        _provider_warning_metadata(warning)
        for warning in response.optimization_warnings
    )
    selected_unit_ids = tuple(record.unit_id for record in selected_units)
    warnings = tuple(warning.code for warning in warning_details)
    metadata = EvalProviderMetadata(
        selected_units=selected_units,
        warning_details=warning_details,
        unresolved_unit_ids=tuple(
            access.access_id for access in response.unresolved_frontier
        ),
        unsupported_unit_ids=tuple(
            construct.construct_id for construct in response.unsupported_constructs
        ),
        syntax_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.syntax_diagnostics
        ),
        semantic_diagnostic_ids=tuple(
            diagnostic.diagnostic_id for diagnostic in response.semantic_diagnostics
        ),
    )
    return EvalProviderResult(
        provider_name=CONTEXT_IR_PROVIDER,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=EvalProviderConfig(),
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        document=response.compile_result.document,
        total_tokens=response.compile_total_tokens,
        selected_files=(),
        omitted_candidate_files=(),
        selected_unit_ids=selected_unit_ids,
        omitted_unit_ids=response.omitted_unit_ids,
        warnings=warnings,
        metadata=metadata,
    )


def build_lexical_top_k_files_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Build the deterministic lexical top-k whole-file baseline pack."""
    scored_files = _score_baseline_files(request.repo_root, request.query)
    positive_candidates = tuple(
        scored.file for scored in scored_files if scored.score > 0.0
    )
    candidate_files = positive_candidates[:LEXICAL_MAX_CANDIDATES]
    warnings: tuple[str, ...] = ()
    if not candidate_files:
        warnings = ("no_positive_lexical_score",)

    packed = _pack_baseline_files(
        baseline_name=LEXICAL_TOP_K_FILES_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=candidate_files,
        warnings=warnings,
    )
    metadata = EvalProviderMetadata(
        candidate_files=tuple(file.relative_path for file in candidate_files),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        lexical_scores=_lexical_score_metadata(scored_files),
    )
    return _baseline_result(
        provider_name=LEXICAL_TOP_K_FILES_PROVIDER,
        config=EvalProviderConfig(max_candidates=LEXICAL_MAX_CANDIDATES),
        request=request,
        packed=packed,
        warnings=warnings,
        metadata=metadata,
    )


def build_import_neighborhood_files_pack(
    request: EvalProviderRequest,
) -> EvalProviderResult:
    """Build the deterministic lexical-seed import-neighborhood baseline pack."""
    repo_root = Path(request.repo_root)
    baseline_files = _discover_baseline_files(repo_root)
    module_to_file = _module_map(baseline_files)
    path_to_module = {
        file.relative_path: module for module, file in module_to_file.items()
    }
    scored_files = _score_files(baseline_files, request.query)
    positive_candidates = tuple(
        scored.file for scored in scored_files if scored.score > 0.0
    )
    seeds = positive_candidates[:IMPORT_SEED_COUNT]
    warnings: list[str] = []
    if not seeds:
        _append_warning(warnings, "no_positive_seed")

    ordered_candidates = _import_neighborhood_candidates(
        seeds=seeds,
        module_to_file=module_to_file,
        path_to_module=path_to_module,
        warnings=warnings,
    )
    warning_tuple = tuple(warnings)
    packed = _pack_baseline_files(
        baseline_name=IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=ordered_candidates,
        warnings=warning_tuple,
    )
    metadata = EvalProviderMetadata(
        candidate_files=tuple(file.relative_path for file in ordered_candidates),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        lexical_scores=_lexical_score_metadata(scored_files),
    )
    return _baseline_result(
        provider_name=IMPORT_NEIGHBORHOOD_FILES_PROVIDER,
        config=EvalProviderConfig(seed_count=IMPORT_SEED_COUNT),
        request=request,
        packed=packed,
        warnings=warning_tuple,
        metadata=metadata,
    )


def build_file_order_floor_pack(request: EvalProviderRequest) -> EvalProviderResult:
    """Build the deterministic file-order diagnostic baseline pack."""
    candidate_files = _discover_baseline_files(Path(request.repo_root))
    packed = _pack_baseline_files(
        baseline_name=FILE_ORDER_FLOOR_PROVIDER,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        candidates=candidate_files,
        warnings=(),
    )
    metadata = EvalProviderMetadata(
        diagnostic_only=True,
        candidate_files=tuple(file.relative_path for file in candidate_files),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
    )
    return _baseline_result(
        provider_name=FILE_ORDER_FLOOR_PROVIDER,
        config=EvalProviderConfig(diagnostic_only=True),
        request=request,
        packed=packed,
        warnings=(),
        metadata=metadata,
    )


@dataclass(frozen=True)
class _PackedBaseline:
    """Budget-packed baseline document and selected file metadata."""

    document: str
    total_tokens: int
    selected: tuple[_BaselineFile, ...]
    omitted: tuple[_BaselineFile, ...]


def _baseline_result(
    *,
    provider_name: str,
    config: EvalProviderConfig,
    request: EvalProviderRequest,
    packed: _PackedBaseline,
    warnings: tuple[str, ...],
    metadata: EvalProviderMetadata,
) -> EvalProviderResult:
    """Build the standard provider result for a whole-file baseline."""
    return EvalProviderResult(
        provider_name=provider_name,
        provider_algorithm_version=PROVIDER_ALGORITHM_VERSION,
        provider_config=config,
        task_id=request.task_id,
        query=request.query,
        budget=request.budget,
        document=packed.document,
        total_tokens=packed.total_tokens,
        selected_files=tuple(file.relative_path for file in packed.selected),
        omitted_candidate_files=tuple(file.relative_path for file in packed.omitted),
        selected_unit_ids=(),
        omitted_unit_ids=(),
        warnings=warnings,
        metadata=metadata,
    )


def _discover_baseline_files(repo_root: Path) -> tuple[_BaselineFile, ...]:
    """Return all regular UTF-8 Python files below ``repo_root`` in path order."""
    discovered: list[_BaselineFile] = []
    for path in sorted(repo_root.rglob("*.py"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative_path = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        discovered.append(
            _BaselineFile(
                relative_path=relative_path,
                text=text,
                token_count=estimate_tokens(text),
            )
        )
    return tuple(sorted(discovered, key=lambda file: file.relative_path))


def _score_baseline_files(
    repo_root: Path | str,
    query: str,
) -> tuple[_ScoredBaselineFile, ...]:
    """Discover and lexically score baseline files for ``query``."""
    return _score_files(_discover_baseline_files(Path(repo_root)), query)


def _score_files(
    files: tuple[_BaselineFile, ...],
    query: str,
) -> tuple[_ScoredBaselineFile, ...]:
    """Return files sorted by lexical baseline candidate order."""
    query_terms = _unique_terms(lexical_tokens(query))
    scored = tuple(_score_file(file, query_terms) for file in files)
    return tuple(
        sorted(
            scored,
            key=lambda scored_file: (
                -scored_file.score,
                scored_file.file.token_count,
                scored_file.file.relative_path,
            ),
        )
    )


def _score_file(
    file: _BaselineFile,
    query_terms: tuple[str, ...],
) -> _ScoredBaselineFile:
    """Score one file according to the frozen lexical baseline formula."""
    content_terms = Counter(lexical_tokens(file.text))
    path_terms = lexical_tokens(file.relative_path)
    if not query_terms:
        score = 0.0
    else:
        content_matches = sum(1 for term in query_terms if content_terms[term] > 0)
        path_matches = sum(1 for term in query_terms if term in path_terms)
        occurrence = min(
            1.0,
            sum(min(content_terms[term], 3) for term in query_terms)
            / (3 * len(query_terms)),
        )
        score = (
            0.75 * (content_matches / len(query_terms))
            + 0.20 * (path_matches / len(query_terms))
            + 0.05 * occurrence
        )
    return _ScoredBaselineFile(
        file=file,
        score=score,
        content_terms=content_terms,
        path_terms=path_terms,
    )


def _unique_terms(terms: tuple[str, ...]) -> tuple[str, ...]:
    """Return lexical terms unique in first-seen order."""
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        unique.append(term)
    return tuple(unique)


def _lexical_score_metadata(
    scored_files: tuple[_ScoredBaselineFile, ...],
) -> tuple[LexicalFileScore, ...]:
    """Return compact lexical score metadata for provider output."""
    return tuple(
        LexicalFileScore(
            file_path=scored.file.relative_path,
            score=scored.score,
            token_count=scored.file.token_count,
        )
        for scored in scored_files
    )


def _pack_baseline_files(
    *,
    baseline_name: str,
    task_id: str,
    query: str,
    budget: int,
    candidates: tuple[_BaselineFile, ...],
    warnings: tuple[str, ...],
) -> _PackedBaseline:
    """Greedily pack whole files while keeping final document tokens in budget."""
    selected: list[_BaselineFile] = []
    for candidate in candidates:
        tentative = tuple([*selected, candidate])
        document = _assemble_baseline_document(
            baseline_name=baseline_name,
            task_id=task_id,
            query=query,
            budget=budget,
            selected_files=tentative,
            omitted_candidate_file_count=len(candidates) - len(tentative),
            warnings=warnings,
        )
        if estimate_tokens(document) <= budget:
            selected.append(candidate)

    selected_tuple = tuple(selected)
    omitted = tuple(
        candidate for candidate in candidates if candidate not in selected_tuple
    )
    document = _assemble_baseline_document(
        baseline_name=baseline_name,
        task_id=task_id,
        query=query,
        budget=budget,
        selected_files=selected_tuple,
        omitted_candidate_file_count=len(omitted),
        warnings=warnings,
    )
    while selected_tuple and estimate_tokens(document) > budget:
        selected_tuple = selected_tuple[:-1]
        omitted = tuple(
            candidate for candidate in candidates if candidate not in selected_tuple
        )
        document = _assemble_baseline_document(
            baseline_name=baseline_name,
            task_id=task_id,
            query=query,
            budget=budget,
            selected_files=selected_tuple,
            omitted_candidate_file_count=len(omitted),
            warnings=warnings,
        )

    total_tokens = estimate_tokens(document)
    if total_tokens > budget:
        raise ValueError(
            f"budget {budget} is too small for {baseline_name} baseline envelope"
        )
    return _PackedBaseline(
        document=document,
        total_tokens=total_tokens,
        selected=selected_tuple,
        omitted=omitted,
    )


def _assemble_baseline_document(
    *,
    baseline_name: str,
    task_id: str,
    query: str,
    budget: int,
    selected_files: tuple[_BaselineFile, ...],
    omitted_candidate_file_count: int,
    warnings: tuple[str, ...],
) -> str:
    """Assemble the accepted baseline document format."""
    lines = [
        "# Baseline Context",
        f"baseline: {baseline_name}",
        f"task_id: {task_id}",
        f"query: {query or '<empty>'}",
        f"budget: {budget}",
        f"selected_files: {len(selected_files)}",
        f"omitted_candidate_files: {omitted_candidate_file_count}",
    ]
    if warnings:
        lines.append(f"warnings: {len(warnings)}")
    document = "\n".join(lines)
    for file in selected_files:
        document = f"{document}\n\n## {file.relative_path}\n{file.text}"
    return document


def _module_map(files: tuple[_BaselineFile, ...]) -> dict[str, _BaselineFile]:
    """Map resolvable repository module names to Python source files."""
    modules: dict[str, _BaselineFile] = {}
    for file in files:
        modules[_module_name(file.relative_path)] = file
    return modules


def _module_name(relative_path: str) -> str:
    """Return the importable module name for one repository-relative path."""
    path = PurePosixPath(relative_path)
    if path.name == "__init__.py":
        if path.parent == PurePosixPath("."):
            return "__init__"
        return ".".join(path.parent.parts)
    return ".".join(path.with_suffix("").parts)


def _import_neighborhood_candidates(
    *,
    seeds: tuple[_BaselineFile, ...],
    module_to_file: dict[str, _BaselineFile],
    path_to_module: dict[str, str],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Return seeds followed by first-hop repo import files."""
    ordered: list[_BaselineFile] = []
    seen_paths: set[str] = set()
    for seed in seeds:
        _append_file(ordered, seen_paths, seed)

    for seed in seeds:
        try:
            tree = ast.parse(seed.text, filename=seed.relative_path)
        except SyntaxError:
            _append_warning(warnings, "import_parse_error")
            continue
        seed_module = path_to_module[seed.relative_path]
        for node in _iter_import_nodes(tree):
            for imported_file in _resolve_import_node(
                source_file=seed,
                source_module=seed_module,
                node=node,
                module_to_file=module_to_file,
                warnings=warnings,
            ):
                _append_file(ordered, seen_paths, imported_file)
    return tuple(ordered)


def _append_file(
    ordered: list[_BaselineFile],
    seen_paths: set[str],
    file: _BaselineFile,
) -> None:
    """Append ``file`` once, preserving first occurrence order."""
    if file.relative_path in seen_paths:
        return
    seen_paths.add(file.relative_path)
    ordered.append(file)


def _iter_import_nodes(tree: ast.AST) -> tuple[ast.Import | ast.ImportFrom, ...]:
    """Return import nodes in deterministic AST preorder traversal."""
    nodes: list[ast.Import | ast.ImportFrom] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Import | ast.ImportFrom):
            nodes.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return tuple(nodes)


def _resolve_import_node(
    *,
    source_file: _BaselineFile,
    source_module: str,
    node: ast.Import | ast.ImportFrom,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve direct repository imports from one import AST node."""
    if isinstance(node, ast.Import):
        return _resolve_import_aliases(node, module_to_file, warnings)
    return _resolve_from_import_aliases(
        source_file=source_file,
        source_module=source_module,
        node=node,
        module_to_file=module_to_file,
        warnings=warnings,
    )


def _resolve_import_aliases(
    node: ast.Import,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve ``import M`` aliases by exact module name only."""
    resolved: list[_BaselineFile] = []
    for alias in node.names:
        imported_file = module_to_file.get(alias.name)
        if imported_file is None:
            _append_warning(warnings, "import_not_resolved")
            continue
        resolved.append(imported_file)
    return tuple(resolved)


def _resolve_from_import_aliases(
    *,
    source_file: _BaselineFile,
    source_module: str,
    node: ast.ImportFrom,
    module_to_file: dict[str, _BaselineFile],
    warnings: list[str],
) -> tuple[_BaselineFile, ...]:
    """Resolve ``from M import name`` aliases against repository modules."""
    base_module = _from_import_base_module(
        source_file=source_file,
        source_module=source_module,
        imported_module=node.module,
        level=node.level,
    )
    if base_module is None:
        _append_warning(warnings, "unsupported_relative_import")
        return ()

    resolved: list[_BaselineFile] = []
    for alias in node.names:
        if alias.name == "*":
            _append_warning(warnings, "star_import_not_expanded")
            imported_file = module_to_file.get(base_module)
            if imported_file is None:
                _append_warning(warnings, "import_not_resolved")
                continue
            resolved.append(imported_file)
            continue

        target_module = f"{base_module}.{alias.name}" if base_module else alias.name
        imported_file = module_to_file.get(target_module)
        if imported_file is None and base_module:
            imported_file = module_to_file.get(base_module)
        if imported_file is None:
            _append_warning(warnings, "import_not_resolved")
            continue
        resolved.append(imported_file)
    return tuple(resolved)


def _from_import_base_module(
    *,
    source_file: _BaselineFile,
    source_module: str,
    imported_module: str | None,
    level: int,
) -> str | None:
    """Resolve the base module for absolute and relative ``from`` imports."""
    if level == 0:
        return imported_module or ""

    current_package = _current_package(source_file.relative_path, source_module)
    parts = [] if not current_package else current_package.split(".")
    ascents = level - 1
    if ascents > len(parts):
        return None
    if ascents:
        parts = parts[:-ascents]
    if imported_module:
        parts.extend(imported_module.split("."))
    return ".".join(parts)


def _current_package(relative_path: str, module_name: str) -> str:
    """Return the current package for resolving a relative import."""
    if PurePosixPath(relative_path).name == "__init__.py":
        return module_name
    if "." not in module_name:
        return ""
    return module_name.rsplit(".", 1)[0]


def _append_warning(warnings: list[str], code: str) -> None:
    """Append a warning code only on its first occurrence."""
    if code not in warnings:
        warnings.append(code)


def _selected_unit_metadata(
    record: SemanticSelectionRecord,
) -> EvalSelectedUnit:
    """Return structured selected-unit metadata from one semantic trace record."""
    return EvalSelectedUnit(
        unit_id=record.unit_id,
        detail=record.detail,
        token_count=record.token_count,
        basis=record.basis.value,
        reason=record.reason,
        edit_score=record.edit_score,
        support_score=record.support_score,
    )


def _provider_warning_metadata(
    warning: SemanticOptimizationWarning,
) -> EvalProviderWarning:
    """Return structured warning metadata from one semantic warning."""
    return EvalProviderWarning(
        code=warning.code.value,
        unit_id=warning.unit_id,
        message=warning.message,
    )


__all__ = [
    "CONTEXT_IR_PROVIDER",
    "FILE_ORDER_FLOOR_PROVIDER",
    "IMPORT_NEIGHBORHOOD_FILES_PROVIDER",
    "IMPORT_SEED_COUNT",
    "LEXICAL_MAX_CANDIDATES",
    "LEXICAL_TOP_K_FILES_PROVIDER",
    "PROVIDER_ALGORITHM_VERSION",
    "EvalProviderConfig",
    "EvalProviderMetadata",
    "EvalProviderRequest",
    "EvalProviderResult",
    "EvalProviderWarning",
    "EvalSelectedUnit",
    "LexicalFileScore",
    "build_context_ir_provider_pack",
    "build_file_order_floor_pack",
    "build_import_neighborhood_files_pack",
    "build_lexical_top_k_files_pack",
    "estimate_tokens",
    "lexical_tokens",
]
