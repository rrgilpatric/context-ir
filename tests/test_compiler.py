"""Integration tests for the compile contract."""

from __future__ import annotations

import tempfile
from pathlib import Path

from context_ir.compiler import compile
from context_ir.parser import parse_repository
from context_ir.types import CompileResult, CompileTraceEntry

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repo"


# ---------------------------------------------------------------------------
# Fake embedder
# ---------------------------------------------------------------------------


def _constant_embed(texts: list[str]) -> list[list[float]]:
    """Returns identical vectors so embeddings contribute zero signal."""
    return [[0.5] * 64 for _ in texts]


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _compile_fixture(
    query: str = "validate_name",
    budget: int = 10_000,
) -> CompileResult:
    """Run compile on the fixture repo with deterministic embeddings."""
    return compile(
        query=query,
        repo_root=FIXTURES,
        budget=budget,
        embed_fn=_constant_embed,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_compile_returns_compile_result() -> None:
    """compile with generous budget returns a CompileResult with all fields."""
    result = _compile_fixture()
    assert isinstance(result, CompileResult)
    assert isinstance(result.document, str)
    assert isinstance(result.trace, list)
    assert isinstance(result.warnings, list)
    assert isinstance(result.omitted_frontier, list)
    assert isinstance(result.confidence, float)
    assert isinstance(result.total_tokens, int)
    assert isinstance(result.budget, int)


def test_compile_document_nonempty() -> None:
    """document string is non-empty for a meaningful query and budget."""
    result = _compile_fixture()
    assert len(result.document) > 0


def test_compile_document_has_header() -> None:
    """document starts with # Compiled Context and includes the query text."""
    result = _compile_fixture()
    assert result.document.startswith("# Compiled Context")
    assert "validate_name" in result.document


def test_compile_document_contains_symbols() -> None:
    """document contains at least one rendered symbol name from the fixture repo."""
    result = _compile_fixture()
    # The fixture repo has validate_name, User, check_length, etc.
    has_symbol = (
        "validate_name" in result.document
        or "User" in result.document
        or "check_length" in result.document
    )
    assert has_symbol


def test_compile_document_grouped_by_file() -> None:
    """Symbols from the same file appear in the same section."""
    result = _compile_fixture()
    doc = result.document
    # The fixture repo has mypackage/models.py with validate_name and User
    assert "## mypackage/models.py" in doc
    # File header should appear before its symbols
    file_header_pos = doc.index("## mypackage/models.py")
    # At least one symbol from models.py should follow the header
    after_header = doc[file_header_pos:]
    has_models_symbol = (
        "validate_name" in after_header
        or "User" in after_header
        or "check_length" in after_header
    )
    assert has_models_symbol


def test_compile_document_shows_tier() -> None:
    """document contains tier labels like [FULL], [STUB], or [SLICE]."""
    result = _compile_fixture()
    doc = result.document
    has_tier = any(
        label in doc for label in ("[FULL]", "[SLICE]", "[STUB]", "[SUMMARY]", "[OMIT]")
    )
    assert has_tier


def test_compile_tight_budget() -> None:
    """Tight budget produces fewer packed symbols and lower confidence."""
    generous = _compile_fixture(budget=10_000)
    tight = _compile_fixture(budget=20)

    # Count non-OMIT tier entries in trace
    generous_packed = sum(
        1
        for e in generous.trace
        if e.chosen_tier.value > 1  # above OMIT
    )
    tight_packed = sum(1 for e in tight.trace if e.chosen_tier.value > 1)
    assert tight_packed <= generous_packed
    assert tight.confidence <= generous.confidence


def test_compile_trace_populated() -> None:
    """trace is a non-empty list of CompileTraceEntry."""
    result = _compile_fixture()
    assert len(result.trace) > 0
    assert all(isinstance(e, CompileTraceEntry) for e in result.trace)


def test_compile_confidence_range() -> None:
    """confidence is in [0.0, 1.0]."""
    result = _compile_fixture()
    assert 0.0 <= result.confidence <= 1.0


def test_compile_budget_recorded() -> None:
    """result.budget matches the input budget."""
    result = _compile_fixture(budget=5_000)
    assert result.budget == 5_000


def test_compile_pre_parsed_graph() -> None:
    """Pass a pre-parsed graph via the graph parameter. Verify the result is valid."""
    graph = parse_repository(FIXTURES)
    result = compile(
        query="validate_name",
        repo_root=FIXTURES,
        budget=10_000,
        embed_fn=_constant_embed,
        graph=graph,
    )
    assert isinstance(result, CompileResult)
    assert len(result.document) > 0
    assert len(result.trace) > 0
    assert 0.0 <= result.confidence <= 1.0


def test_compile_empty_repo() -> None:
    """compile on an empty temp directory returns a valid minimal CompileResult."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = compile(
            query="anything",
            repo_root=Path(tmpdir),
            budget=10_000,
            embed_fn=_constant_embed,
        )
        assert isinstance(result, CompileResult)
        assert result.document.startswith("# Compiled Context")
        assert result.trace == []
        assert result.confidence == 1.0
