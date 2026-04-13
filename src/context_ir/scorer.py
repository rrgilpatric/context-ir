"""Scoring engine for symbol graph relevance scoring.

Computes p_edit and p_support for every node in a SymbolGraph given a
natural language query. Uses four feature types: lexical matching,
structural priors, semantic similarity, and graph propagation.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from pathlib import Path

from context_ir.types import (
    EdgeKind,
    EditSupportScores,
    SymbolGraph,
    SymbolKind,
    SymbolNode,
)

# ---------------------------------------------------------------------------
# Feature weight constants (tunable later via eval, Slice 9)
# ---------------------------------------------------------------------------

W_LEX_EDIT: float = 0.40
W_STRUCT_EDIT: float = 0.10
W_SEM_EDIT: float = 0.50

W_LEX_SUPPORT: float = 0.30
W_STRUCT_SUPPORT: float = 0.20
W_SEM_SUPPORT: float = 0.50

PROPAGATION_DECAY: float = 0.3
PROPAGATION_ITERATIONS: int = 2

# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_model: object | None = None


def _get_default_embed_fn() -> Callable[[list[str]], list[list[float]]]:
    """Return the default embedding function, loading the model on first call."""

    def _embed(texts: list[str]) -> list[list[float]]:
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = _model.encode(texts)  # type: ignore[union-attr]
        result: list[list[float]] = embeddings.tolist()
        return result

    return _embed


# ---------------------------------------------------------------------------
# Cosine similarity (pure Python)
# ---------------------------------------------------------------------------


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Step 1: Query term extraction
# ---------------------------------------------------------------------------

_SPLIT_RE: re.Pattern[str] = re.compile(r"[^\w./]+")


def _extract_query_terms(query: str) -> list[str]:
    """Tokenize the query into terms for lexical matching.

    Splits on whitespace and punctuation, extracts Python identifiers
    (snake_case parts, CamelCase parts) and file path fragments,
    lowercases all terms. Returns deduplicated terms preserving
    insertion order.
    """
    if not query.strip():
        return []
    raw_tokens = _SPLIT_RE.split(query)
    seen: set[str] = set()
    terms: list[str] = []

    for token in raw_tokens:
        token = token.strip()
        if not token:
            continue
        low = token.lower()
        if low not in seen:
            terms.append(low)
            seen.add(low)
        # Split snake_case into parts
        if "_" in token:
            for part in token.split("_"):
                if part:
                    part_low = part.lower()
                    if part_low not in seen:
                        terms.append(part_low)
                        seen.add(part_low)
        # Split CamelCase into parts
        camel_parts = re.findall(r"[A-Z][a-z]+|[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", token)
        for part in camel_parts:
            part_low = part.lower()
            if part_low not in seen:
                terms.append(part_low)
                seen.add(part_low)

    return terms


# ---------------------------------------------------------------------------
# Step 2: Build symbol text profiles
# ---------------------------------------------------------------------------


def _build_text_profiles(
    graph: SymbolGraph,
    repo_root: Path,
) -> dict[str, str]:
    """Build short text profiles for each node for embedding.

    Combines symbol name, file path, and (for callables/classes)
    the signature line and docstring first line.
    """
    file_cache: dict[str, list[str]] = {}
    profiles: dict[str, str] = {}

    for node_id, node in graph.nodes.items():
        parts: list[str] = [node.name, node.file_path]

        if node.kind in (
            SymbolKind.FUNCTION,
            SymbolKind.METHOD,
            SymbolKind.CLASS,
        ):
            lines = _get_file_lines(node.file_path, repo_root, file_cache)
            if lines is not None and node.start_line >= 1:
                source_lines = lines[node.start_line - 1 : node.end_line]
                if source_lines:
                    parts.append(source_lines[0].strip())
                    doc_line = _extract_first_docstring_line(source_lines)
                    if doc_line:
                        parts.append(doc_line)

        profiles[node_id] = " ".join(parts)

    return profiles


def _get_file_lines(
    rel_path: str,
    repo_root: Path,
    cache: dict[str, list[str]],
) -> list[str] | None:
    """Read file lines with caching. Returns None on read failure."""
    if rel_path in cache:
        return cache[rel_path]
    try:
        text = (repo_root / rel_path).read_text()
        lines = text.splitlines()
        cache[rel_path] = lines
        return lines
    except OSError:
        return None


def _extract_first_docstring_line(source_lines: list[str]) -> str | None:
    """Extract the first content line of a docstring from source lines.

    Looks for a triple-quoted string as the first non-empty statement
    after the def/class line.
    """
    for i, line in enumerate(source_lines):
        stripped = line.strip()
        if i == 0:
            continue
        if not stripped:
            continue
        for quote in ('"""', "'''"):
            if stripped.startswith(quote):
                content = stripped[len(quote) :]
                if content.endswith(quote) and len(content) >= len(quote):
                    return content[: -len(quote)].strip() or None
                return content.strip() or None
        break
    return None


# ---------------------------------------------------------------------------
# Step 3: Lexical scoring
# ---------------------------------------------------------------------------


def _compute_lexical_scores(
    query_terms: list[str],
    graph: SymbolGraph,
    repo_root: Path,
) -> dict[str, tuple[float, float]]:
    """Compute lexical edit and support scores for each node.

    Returns a dict mapping node_id to (lexical_edit, lexical_support).
    """
    if not query_terms:
        return {nid: (0.0, 0.0) for nid in graph.nodes}

    file_cache: dict[str, list[str]] = {}
    scores: dict[str, tuple[float, float]] = {}

    for node_id, node in graph.nodes.items():
        name_lower = node.name.lower()
        path_lower = node.file_path.lower()
        filename_lower = Path(node.file_path).name.lower()

        name_match = _compute_name_match(query_terms, name_lower)
        path_match = _compute_path_match(query_terms, path_lower, filename_lower)
        content_match = _compute_content_match(query_terms, node, repo_root, file_cache)

        # Name and path matches are strong edit signals.
        # Content matches contribute more to support.
        lexical_edit = name_match * 0.6 + path_match * 0.2 + content_match * 0.2
        lexical_support = name_match * 0.2 + path_match * 0.3 + content_match * 0.5

        scores[node_id] = (lexical_edit, lexical_support)

    return scores


def _compute_name_match(query_terms: list[str], name_lower: str) -> float:
    """Compute name match score between query terms and a symbol name."""
    best = 0.0
    for term in query_terms:
        if term == name_lower:
            return 1.0
        if len(term) >= 3 and (term in name_lower or name_lower in term):
            best = max(best, 0.5)
    return best


def _compute_path_match(
    query_terms: list[str],
    path_lower: str,
    filename_lower: str,
) -> float:
    """Compute path match score between query terms and a file path."""
    best = 0.0
    for term in query_terms:
        if term in (path_lower, filename_lower):
            return 1.0
        if term in path_lower or term in filename_lower:
            if "/" in term or term.endswith(".py"):
                best = max(best, 0.8)
            else:
                best = max(best, 0.6)
        # Try dots replaced by slashes (Python module paths)
        normalized = term.replace(".", "/")
        if normalized != term and normalized in path_lower:
            best = max(best, 0.8)
    return best


def _compute_content_match(
    query_terms: list[str],
    node: SymbolNode,
    repo_root: Path,
    file_cache: dict[str, list[str]],
) -> float:
    """Compute content match score for query terms in a node's source."""
    if node.kind not in (
        SymbolKind.FUNCTION,
        SymbolKind.METHOD,
        SymbolKind.CLASS,
        SymbolKind.CONSTANT,
    ):
        return 0.0
    lines = _get_file_lines(node.file_path, repo_root, file_cache)
    if lines is None or node.start_line < 1:
        return 0.0
    source = "\n".join(lines[node.start_line - 1 : node.end_line]).lower()
    matches = sum(1 for t in query_terms if t in source)
    return min(matches / len(query_terms), 1.0)


# ---------------------------------------------------------------------------
# Step 4: Structural priors
# ---------------------------------------------------------------------------


def _compute_structural_priors(
    graph: SymbolGraph,
) -> dict[str, tuple[float, float]]:
    """Compute structural edit and support priors for each node.

    Returns a dict mapping node_id to (structural_edit, structural_support).
    """
    scores: dict[str, tuple[float, float]] = {}

    for node_id, node in graph.nodes.items():
        path_lower = node.file_path.lower()
        edit = 0.0
        support = 0.0

        is_test = "test_" in path_lower or "/tests/" in path_lower
        is_config = any(kw in path_lower for kw in ("config", "settings", "conf"))
        is_entry = any(kw in path_lower for kw in ("main.py", "app.py", "__main__"))

        # Base priors by kind
        if node.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD):
            edit = 0.3
            support = 0.2
        elif node.kind == SymbolKind.CLASS:
            edit = 0.25
            support = 0.2
        elif node.kind == SymbolKind.CONSTANT:
            edit = 0.1
            support = 0.15
        elif node.kind == SymbolKind.IMPORT:
            edit = 0.05
            support = 0.1
        elif node.kind in (SymbolKind.FILE, SymbolKind.MODULE):
            edit = 0.1
            support = 0.1

        # Contextual adjustments
        if is_test:
            support += 0.2
            edit *= 0.5
        if is_config:
            support += 0.15
        if is_entry:
            edit += 0.15

        scores[node_id] = (min(edit, 1.0), min(support, 1.0))

    return scores


# ---------------------------------------------------------------------------
# Step 5: Semantic similarity
# ---------------------------------------------------------------------------


def _compute_semantic_scores(
    query: str,
    profiles: dict[str, str],
    embed_fn: Callable[[list[str]], list[list[float]]],
) -> dict[str, float]:
    """Compute semantic similarity between query and each node profile.

    Returns a dict mapping node_id to similarity score in [0, 1].
    """
    if not profiles:
        return {}

    node_ids = list(profiles.keys())
    texts = [query] + [profiles[nid] for nid in node_ids]
    embeddings = embed_fn(texts)

    query_vec = embeddings[0]
    scores: dict[str, float] = {}
    for i, node_id in enumerate(node_ids):
        sim = _cosine_similarity(query_vec, embeddings[i + 1])
        scores[node_id] = max(0.0, sim)

    return scores


# ---------------------------------------------------------------------------
# Step 6: Combine initial scores
# ---------------------------------------------------------------------------


def _combine_initial_scores(
    lexical: dict[str, tuple[float, float]],
    structural: dict[str, tuple[float, float]],
    semantic: dict[str, float],
) -> dict[str, tuple[float, float]]:
    """Combine feature scores into initial p_edit and p_support.

    Returns a dict mapping node_id to (p_edit, p_support).
    """
    combined: dict[str, tuple[float, float]] = {}

    for node_id in lexical:
        lex_edit, lex_support = lexical[node_id]
        struct_edit, struct_support = structural.get(node_id, (0.0, 0.0))
        sem = semantic.get(node_id, 0.0)

        p_edit = W_LEX_EDIT * lex_edit + W_STRUCT_EDIT * struct_edit + W_SEM_EDIT * sem
        p_support = (
            W_LEX_SUPPORT * lex_support
            + W_STRUCT_SUPPORT * struct_support
            + W_SEM_SUPPORT * sem
        )
        combined[node_id] = (p_edit, p_support)

    return combined


# ---------------------------------------------------------------------------
# Step 7: Graph propagation (2 iterations with dampening)
# ---------------------------------------------------------------------------


def _propagate_scores(
    scores: dict[str, tuple[float, float]],
    graph: SymbolGraph,
) -> dict[str, tuple[float, float]]:
    """Spread scores along graph edges for 2 iterations.

    CALLS/IMPORTS: high p_edit on source boosts target p_support.
    DEFINES (parent defines child): high p_edit on child boosts parent p_edit.
    Decay factor per hop: 0.3.
    """
    current = dict(scores)

    for _ in range(PROPAGATION_ITERATIONS):
        deltas: dict[str, tuple[float, float]] = {nid: (0.0, 0.0) for nid in current}

        for edge in graph.edges:
            src = edge.source_id
            tgt = edge.target_id
            if src not in current or tgt not in current:
                continue

            src_edit = current[src][0]
            tgt_edit = current[tgt][0]

            if edge.kind in (EdgeKind.CALLS, EdgeKind.IMPORTS):
                # If source has high p_edit, target gets p_support boost
                boost = PROPAGATION_DECAY * src_edit
                old_e, old_s = deltas[tgt]
                deltas[tgt] = (old_e, old_s + boost)

            elif edge.kind == EdgeKind.DEFINES:
                # If child has high p_edit, parent gets p_edit boost
                boost = PROPAGATION_DECAY * tgt_edit
                old_e, old_s = deltas[src]
                deltas[src] = (old_e + boost, old_s)

        # Apply deltas
        for nid in current:
            old_edit, old_support = current[nid]
            d_edit, d_support = deltas[nid]
            current[nid] = (old_edit + d_edit, old_support + d_support)

    return current


# ---------------------------------------------------------------------------
# Step 8: Container node scoring
# ---------------------------------------------------------------------------


def _score_container_nodes(
    scores: dict[str, tuple[float, float]],
    graph: SymbolGraph,
) -> dict[str, tuple[float, float]]:
    """Set FILE and MODULE scores to the max of their children's scores."""
    children_map: dict[str, list[str]] = {}
    for node_id, node in graph.nodes.items():
        if node.parent_id is not None and node.parent_id in graph.nodes:
            if node.parent_id not in children_map:
                children_map[node.parent_id] = []
            children_map[node.parent_id].append(node_id)

    result = dict(scores)

    for node_id, node in graph.nodes.items():
        if node.kind not in (SymbolKind.FILE, SymbolKind.MODULE):
            continue
        child_ids = children_map.get(node_id, [])
        if not child_ids:
            continue
        max_edit = max(result.get(cid, (0.0, 0.0))[0] for cid in child_ids)
        max_support = max(result.get(cid, (0.0, 0.0))[1] for cid in child_ids)
        result[node_id] = (max_edit, max_support)

    return result


# ---------------------------------------------------------------------------
# Step 9: Normalize and clamp
# ---------------------------------------------------------------------------


def _normalize_scores(
    scores: dict[str, tuple[float, float]],
) -> dict[str, EditSupportScores]:
    """Clamp all scores to [0.0, 1.0] and return EditSupportScores."""
    result: dict[str, EditSupportScores] = {}
    for node_id, (p_edit, p_support) in scores.items():
        result[node_id] = EditSupportScores(
            p_edit=max(0.0, min(1.0, p_edit)),
            p_support=max(0.0, min(1.0, p_support)),
        )
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_graph(
    query: str,
    graph: SymbolGraph,
    repo_root: Path,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> dict[str, EditSupportScores]:
    """Score all nodes in the graph for relevance to the query.

    Computes p_edit (probability this unit is part of the edit locus)
    and p_support (probability this unit is supporting context) for
    every node, using lexical matching, structural priors, semantic
    similarity, and graph propagation.

    If embed_fn is None, uses sentence-transformers (all-MiniLM-L6-v2)
    with lazy model loading. Pass a custom embed_fn for testing or
    alternative backends.

    embed_fn signature: takes a list of strings, returns a list of
    float vectors (one per input string).
    """
    if embed_fn is None:
        embed_fn = _get_default_embed_fn()

    # Step 1: Extract query terms for lexical matching
    query_terms = _extract_query_terms(query)

    # Step 2: Build text profiles for semantic embedding
    profiles = _build_text_profiles(graph, repo_root)

    # Step 3: Compute lexical scores
    lexical = _compute_lexical_scores(query_terms, graph, repo_root)

    # Step 4: Compute structural priors
    structural = _compute_structural_priors(graph)

    # Step 5: Compute semantic similarity
    semantic = _compute_semantic_scores(query, profiles, embed_fn)

    # Step 6: Combine into initial p_edit and p_support
    combined = _combine_initial_scores(lexical, structural, semantic)

    # Step 7: Graph propagation (2 iterations)
    propagated = _propagate_scores(combined, graph)

    # Step 8: Container node scoring (FILE/MODULE)
    with_containers = _score_container_nodes(propagated, graph)

    # Step 9: Normalize and clamp to [0.0, 1.0]
    return _normalize_scores(with_containers)
