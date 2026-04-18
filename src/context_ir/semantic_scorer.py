"""Semantic-first ranking for renderable semantic units."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TypeAlias

from context_ir.semantic_renderer import (
    RenderDetail,
    RenderedUnitKind,
    render_semantic_unit,
)
from context_ir.semantic_types import (
    ResolvedSymbol,
    ResolvedSymbolKind,
    SemanticDependency,
    SemanticProgram,
)

EmbeddingFunction: TypeAlias = Callable[[list[str]], list[list[float]]]

_TOKEN_SPLIT_RE = re.compile(r"[^A-Za-z0-9]+")
_CAMEL_CASE_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z]?[a-z]+|[0-9]+")
_DIRECT_SUPPORT_WEIGHT = 0.30
_SEMANTIC_EDIT_WEIGHT = 0.20
_SEMANTIC_SUPPORT_WEIGHT = 0.20
_MIN_RELEVANCE = 0.05
_DEPENDENCY_SUPPORT_WEIGHT = 0.50
_UNCERTAINTY_SCOPE_SUPPORT_WEIGHT = 0.40
_ORCHESTRATION_EDIT_WEIGHT = 0.12
_ORCHESTRATION_MIN_DEPENDENCIES = 2
_ORCHESTRATION_RELEVANCE_THRESHOLD = 0.15
_BODY_SIGNAL_OVERLAP_WEIGHT = 0.55
_BODY_SIGNAL_BIGRAM_WEIGHT = 0.15
_NON_SIGNAL_QUERY_TERMS = frozenset(
    {
        "a",
        "an",
        "and",
        "by",
        "change",
        "fix",
        "for",
        "from",
        "in",
        "keep",
        "keeping",
        "modify",
        "of",
        "on",
        "or",
        "the",
        "to",
        "update",
        "while",
        "with",
        "without",
    }
)
_BODY_SIGNAL_KINDS = frozenset(
    {
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.CLASS,
        ResolvedSymbolKind.METHOD,
    }
)


@dataclass(frozen=True)
class SemanticUnitScore:
    """Ranking policy output for one semantic unit."""

    unit_id: str
    p_edit: float
    p_support: float

    def __post_init__(self) -> None:
        """Keep score records concrete and bounded."""
        if not self.unit_id:
            raise ValueError("unit_id must be non-empty")
        if not _is_probability(self.p_edit):
            raise ValueError("p_edit must be within [0.0, 1.0]")
        if not _is_probability(self.p_support):
            raise ValueError("p_support must be within [0.0, 1.0]")


@dataclass(frozen=True)
class SemanticScoringResult:
    """Minimal scorer output kept separate from ``SemanticProgram``."""

    query: str
    scores: Mapping[str, SemanticUnitScore]

    def __post_init__(self) -> None:
        """Validate score-key integrity and materialize a stable score mapping."""
        normalized_scores = dict(self.scores)
        for unit_id, score in normalized_scores.items():
            if unit_id != score.unit_id:
                raise ValueError(
                    "score mapping keys must match SemanticUnitScore.unit_id"
                )
        object.__setattr__(self, "scores", normalized_scores)


@dataclass(frozen=True)
class _CandidateProfile:
    """Semantic-first text profile for one renderable unit."""

    unit_id: str
    kind: RenderedUnitKind
    primary_text: str
    file_path: str
    scope_id: str | None
    searchable_text: str
    body_text: str | None


def score_semantic_units(
    program: SemanticProgram,
    query: str,
    *,
    embed_fn: EmbeddingFunction | None = None,
) -> SemanticScoringResult:
    """Score every renderable semantic unit without mutating ``program``."""
    candidates = _build_candidate_profiles(program)
    direct_scores = _direct_scores_for_candidates(
        query=query,
        candidates=candidates,
        embed_fn=embed_fn,
    )
    direct_scores = _apply_orchestration_edit_signal(
        scores=direct_scores,
        dependencies=program.proven_dependencies,
    )
    final_scores = dict(direct_scores)
    final_scores = _apply_dependency_support(
        scores=final_scores,
        direct_scores=direct_scores,
        dependencies=program.proven_dependencies,
    )
    final_scores = _apply_scope_support(
        scores=final_scores,
        direct_scores=direct_scores,
        candidates=candidates,
    )
    return SemanticScoringResult(query=query, scores=final_scores)


def _build_candidate_profiles(program: SemanticProgram) -> list[_CandidateProfile]:
    """Build stable semantic-first text profiles for every renderable unit."""
    candidates: list[_CandidateProfile] = []

    for unit_id, symbol in sorted(program.resolved_symbols.items()):
        summary = render_semantic_unit(program, unit_id, RenderDetail.SUMMARY)
        body_text = _body_text_for_symbol(program, unit_id, symbol)
        candidates.append(
            _CandidateProfile(
                unit_id=unit_id,
                kind=summary.kind,
                primary_text=symbol.qualified_name,
                file_path=symbol.definition_site.file_path,
                scope_id=None,
                searchable_text=_join_searchable_text(
                    symbol.qualified_name,
                    symbol.definition_site.file_path,
                    summary.content,
                ),
                body_text=body_text,
            )
        )

    for access in sorted(program.unresolved_frontier, key=lambda item: item.access_id):
        summary = render_semantic_unit(program, access.access_id, RenderDetail.SUMMARY)
        candidates.append(
            _CandidateProfile(
                unit_id=access.access_id,
                kind=summary.kind,
                primary_text=access.access_text,
                file_path=access.site.file_path,
                scope_id=access.enclosing_scope_id,
                searchable_text=_join_searchable_text(
                    access.access_text,
                    access.site.file_path,
                    access.reason_code.value,
                    access.context.value,
                    access.detail,
                    summary.content,
                ),
                body_text=None,
            )
        )

    for construct in sorted(
        program.unsupported_constructs,
        key=lambda item: item.construct_id,
    ):
        summary = render_semantic_unit(
            program,
            construct.construct_id,
            RenderDetail.SUMMARY,
        )
        candidates.append(
            _CandidateProfile(
                unit_id=construct.construct_id,
                kind=summary.kind,
                primary_text=construct.construct_text,
                file_path=construct.site.file_path,
                scope_id=construct.enclosing_scope_id,
                searchable_text=_join_searchable_text(
                    construct.construct_text,
                    construct.site.file_path,
                    construct.reason_code.value,
                    construct.detail,
                    summary.content,
                ),
                body_text=None,
            )
        )

    return candidates


def _direct_scores_for_candidates(
    *,
    query: str,
    candidates: list[_CandidateProfile],
    embed_fn: EmbeddingFunction | None,
) -> dict[str, SemanticUnitScore]:
    """Return deterministic direct-match scores for every candidate."""
    query_terms = _extract_terms(query)
    if not query_terms:
        return {
            candidate.unit_id: SemanticUnitScore(
                unit_id=candidate.unit_id,
                p_edit=0.0,
                p_support=0.0,
            )
            for candidate in candidates
        }

    normalized_query = _normalize_text(query)
    semantic_similarities = _semantic_similarity_by_unit(
        query=query,
        candidates=candidates,
        embed_fn=embed_fn,
    )
    scores: dict[str, SemanticUnitScore] = {}

    for candidate in candidates:
        lexical_score = _lexical_relevance(
            candidate=candidate,
            query_terms=query_terms,
            normalized_query=normalized_query,
        )
        semantic_score = semantic_similarities.get(candidate.unit_id, 0.0)
        p_edit = _clamp_probability(
            lexical_score * (1.0 - _SEMANTIC_EDIT_WEIGHT)
            + semantic_score * _SEMANTIC_EDIT_WEIGHT
        )
        p_support = _clamp_probability(
            lexical_score * _DIRECT_SUPPORT_WEIGHT
            + semantic_score * _SEMANTIC_SUPPORT_WEIGHT
        )
        scores[candidate.unit_id] = SemanticUnitScore(
            unit_id=candidate.unit_id,
            p_edit=p_edit,
            p_support=p_support,
        )

    return scores


def _semantic_similarity_by_unit(
    *,
    query: str,
    candidates: list[_CandidateProfile],
    embed_fn: EmbeddingFunction | None,
) -> dict[str, float]:
    """Return optional embedding-based similarities keyed by unit ID."""
    if embed_fn is None or not candidates:
        return {}

    texts = [query, *(candidate.searchable_text for candidate in candidates)]
    embeddings = embed_fn(texts)
    if len(embeddings) != len(texts):
        raise ValueError("embed_fn must return one embedding per input text")

    query_embedding = embeddings[0]
    similarities: dict[str, float] = {}
    for candidate, embedding in zip(candidates, embeddings[1:], strict=True):
        similarities[candidate.unit_id] = _clamp_probability(
            max(0.0, _cosine_similarity(query_embedding, embedding))
        )
    return similarities


def _lexical_relevance(
    *,
    candidate: _CandidateProfile,
    query_terms: tuple[str, ...],
    normalized_query: str,
) -> float:
    """Return direct lexical relevance from semantic-first text surfaces."""
    primary_terms = frozenset(_extract_terms(candidate.primary_text))
    searchable_terms = frozenset(_extract_terms(candidate.searchable_text))
    path_terms = frozenset(_extract_terms(candidate.file_path))
    focus_terms = _focus_terms(query_terms)
    normalized_primary = _normalize_text(candidate.primary_text)
    normalized_searchable = _normalize_text(candidate.searchable_text)

    primary_phrase = _phrase_match(
        normalized_query=normalized_query,
        normalized_text=normalized_primary,
    )
    searchable_phrase = _phrase_match(
        normalized_query=normalized_query,
        normalized_text=normalized_searchable,
    )
    primary_overlap = _term_overlap(query_terms, primary_terms)
    searchable_overlap = _term_overlap(query_terms, searchable_terms)
    path_overlap = _term_overlap(query_terms, path_terms)
    lexical_score = _clamp_probability(
        primary_phrase * 0.45
        + searchable_phrase * 0.15
        + primary_overlap * 0.25
        + searchable_overlap * 0.10
        + path_overlap * 0.05
    )
    if candidate.body_text is None:
        return lexical_score

    body_terms = _extract_terms(candidate.body_text)
    if not body_terms:
        return lexical_score

    return _clamp_probability(
        lexical_score
        + _term_overlap(focus_terms, frozenset(body_terms))
        * _BODY_SIGNAL_OVERLAP_WEIGHT
        + _ngram_overlap(focus_terms, body_terms, n=2) * _BODY_SIGNAL_BIGRAM_WEIGHT
    )


def _apply_dependency_support(
    *,
    scores: dict[str, SemanticUnitScore],
    direct_scores: Mapping[str, SemanticUnitScore],
    dependencies: list[SemanticDependency],
) -> dict[str, SemanticUnitScore]:
    """Raise support on proven dependency targets from directly relevant sources."""
    updated_scores = dict(scores)
    for dependency in dependencies:
        source_score = direct_scores.get(dependency.source_symbol_id)
        target_score = updated_scores.get(dependency.target_symbol_id)
        if source_score is None or target_score is None:
            continue
        if source_score.p_edit <= 0.0:
            continue
        boost = source_score.p_edit * _DEPENDENCY_SUPPORT_WEIGHT
        updated_scores[dependency.target_symbol_id] = SemanticUnitScore(
            unit_id=target_score.unit_id,
            p_edit=target_score.p_edit,
            p_support=_merge_support(target_score.p_support, boost),
        )
    return updated_scores


def _apply_orchestration_edit_signal(
    *,
    scores: dict[str, SemanticUnitScore],
    dependencies: list[SemanticDependency],
) -> dict[str, SemanticUnitScore]:
    """Boost edit likelihood for symbols coordinating multiple relevant targets."""
    dependency_relevance: dict[str, dict[str, float]] = {}
    for dependency in dependencies:
        source_score = scores.get(dependency.source_symbol_id)
        target_score = scores.get(dependency.target_symbol_id)
        if source_score is None or target_score is None:
            continue
        if source_score.p_edit < _MIN_RELEVANCE:
            continue

        strongest_target_relevance = max(target_score.p_edit, target_score.p_support)
        if strongest_target_relevance < _ORCHESTRATION_RELEVANCE_THRESHOLD:
            continue

        dependency_relevance.setdefault(dependency.source_symbol_id, {})[
            dependency.target_symbol_id
        ] = strongest_target_relevance

    updated_scores = dict(scores)
    for source_symbol_id, target_relevance in dependency_relevance.items():
        if len(target_relevance) < _ORCHESTRATION_MIN_DEPENDENCIES:
            continue

        source_score = updated_scores[source_symbol_id]
        boost = (
            sum(target_relevance.values()) / len(target_relevance)
        ) * _ORCHESTRATION_EDIT_WEIGHT
        updated_scores[source_symbol_id] = SemanticUnitScore(
            unit_id=source_score.unit_id,
            p_edit=_clamp_probability(source_score.p_edit + boost),
            p_support=source_score.p_support,
        )

    return updated_scores


def _apply_scope_support(
    *,
    scores: dict[str, SemanticUnitScore],
    direct_scores: Mapping[str, SemanticUnitScore],
    candidates: list[_CandidateProfile],
) -> dict[str, SemanticUnitScore]:
    """Raise support on unresolved or unsupported units from relevant scopes."""
    updated_scores = dict(scores)
    for candidate in candidates:
        if (
            candidate.kind is RenderedUnitKind.PROVEN_SYMBOL
            or candidate.scope_id is None
        ):
            continue
        scope_score = direct_scores.get(candidate.scope_id)
        target_score = updated_scores.get(candidate.unit_id)
        if scope_score is None or target_score is None:
            continue
        if scope_score.p_edit <= 0.0:
            continue
        boost = scope_score.p_edit * _UNCERTAINTY_SCOPE_SUPPORT_WEIGHT
        updated_scores[candidate.unit_id] = SemanticUnitScore(
            unit_id=target_score.unit_id,
            p_edit=target_score.p_edit,
            p_support=_merge_support(target_score.p_support, boost),
        )
    return updated_scores


def _phrase_match(*, normalized_query: str, normalized_text: str) -> float:
    """Return a strong direct-match score for whole-query lexical alignment."""
    if not normalized_query or not normalized_text:
        return 0.0
    if normalized_query == normalized_text:
        return 1.0
    if normalized_query in normalized_text:
        return 0.85
    return 0.0


def _term_overlap(
    query_terms: tuple[str, ...],
    candidate_terms: frozenset[str],
) -> float:
    """Return the fraction of query terms present in ``candidate_terms``."""
    if not query_terms:
        return 0.0
    matches = sum(1 for term in query_terms if term in candidate_terms)
    return matches / len(query_terms)


def _normalize_text(text: str) -> str:
    """Normalize ``text`` into a whitespace-joined lexical surface."""
    return " ".join(_extract_terms(text))


def _extract_terms(text: str) -> tuple[str, ...]:
    """Extract stable lexical terms from identifiers, paths, and summaries."""
    if not text:
        return ()

    seen: set[str] = set()
    terms: list[str] = []
    for raw_token in _TOKEN_SPLIT_RE.split(text):
        if not raw_token:
            continue
        token_variants = [raw_token]
        camel_parts = _CAMEL_CASE_RE.findall(raw_token)
        token_variants.extend(camel_parts)
        for variant in token_variants:
            normalized = variant.lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            terms.append(normalized)
    return tuple(terms)


def _focus_terms(query_terms: tuple[str, ...]) -> tuple[str, ...]:
    """Return query terms with common instruction glue removed."""
    focused_terms = tuple(
        term for term in query_terms if term not in _NON_SIGNAL_QUERY_TERMS
    )
    if focused_terms:
        return focused_terms
    return query_terms


def _ngram_overlap(
    query_terms: tuple[str, ...],
    candidate_terms: tuple[str, ...],
    *,
    n: int,
) -> float:
    """Return the fraction of query n-grams that appear in ``candidate_terms``."""
    if len(query_terms) < n or len(candidate_terms) < n:
        return 0.0

    query_ngrams = {
        tuple(query_terms[index : index + n])
        for index in range(len(query_terms) - n + 1)
    }
    if not query_ngrams:
        return 0.0

    candidate_ngrams = {
        tuple(candidate_terms[index : index + n])
        for index in range(len(candidate_terms) - n + 1)
    }
    return len(query_ngrams & candidate_ngrams) / len(query_ngrams)


def _body_text_for_symbol(
    program: SemanticProgram,
    unit_id: str,
    symbol: ResolvedSymbol,
) -> str | None:
    """Return source-backed body text for scope-defining symbols only."""
    if symbol.kind not in _BODY_SIGNAL_KINDS:
        return None
    return render_semantic_unit(program, unit_id, RenderDetail.SOURCE).content


def _join_searchable_text(*parts: str | None) -> str:
    """Join optional profile parts without introducing placeholder text."""
    return "\n".join(part for part in parts if part)


def _merge_support(current_support: float, boost: float) -> float:
    """Combine independent support evidence with saturation at one."""
    return _clamp_probability(current_support + boost * (1.0 - current_support))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for embedding injection tests or adapters."""
    dot_product = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot_product / (left_norm * right_norm)


def _clamp_probability(value: float) -> float:
    """Clamp ``value`` into the closed probability interval."""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _is_probability(value: float) -> bool:
    """Return whether ``value`` is a closed-interval probability."""
    return 0.0 <= value <= 1.0


__all__ = [
    "SemanticScoringResult",
    "SemanticUnitScore",
    "score_semantic_units",
]
