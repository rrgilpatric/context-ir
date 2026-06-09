"""Internal real-OSS BM25 baseline contract tests."""

from __future__ import annotations

import inspect
import math
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import context_ir
import context_ir.real_oss_thesis_bm25 as bm25


def _numbered_text(line_count: int) -> str:
    """Return raw text with one numbered content line per requested line."""
    return "".join(f"line {line_number}\n" for line_number in range(1, line_count + 1))


def _chunk(
    repo_path: str,
    start_line: int,
    text: str,
) -> bm25.RealOssBaselineChunk:
    """Return a valid chunk with line range derived from text."""
    line_count = len(text.splitlines(keepends=True))
    return bm25.RealOssBaselineChunk(
        repo_path=repo_path,
        start_line=start_line,
        end_line=start_line + line_count - 1,
        text=text,
    )


def _run_git(repo_root: Path, *args: str) -> None:
    """Run a quiet git command in a test repository."""
    subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=True,
        capture_output=True,
        text=True,
    )


def test_chunking_uses_frozen_line_target_overlap_and_stable_ids() -> None:
    """Raw file text chunks use 160 lines, 40 overlap, and path/range identity."""
    file_text = bm25.RealOssBaselineFileText(
        repo_path="src/pkg/module.py",
        text=_numbered_text(201),
    )

    chunks = bm25.chunk_real_oss_file_text(file_text)

    assert len(chunks) == 2
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 160
    assert chunks[0].line_count == 160
    assert chunks[0].chunk_id == "src/pkg/module.py:1-160"
    assert chunks[0].text.startswith("line 1\n")
    assert chunks[0].text.endswith("line 160\n")
    assert chunks[1].start_line == 121
    assert chunks[1].end_line == 201
    assert chunks[1].line_count == 81
    assert chunks[1].chunk_id == "src/pkg/module.py:121-201"
    assert chunks[1].text.startswith("line 121\n")
    assert chunks[1].text.endswith("line 201\n")


def test_chunk_collection_orders_by_path_then_start_line() -> None:
    """Chunk collection is deterministic even when input files are unsorted."""
    file_texts = (
        bm25.RealOssBaselineFileText("src/z.py", _numbered_text(161)),
        bm25.RealOssBaselineFileText("src/a.py", _numbered_text(1)),
    )

    chunks = bm25.chunk_real_oss_file_texts(file_texts)

    assert tuple(chunk.chunk_id for chunk in chunks) == (
        "src/a.py:1-1",
        "src/z.py:1-160",
        "src/z.py:121-161",
    )


def test_file_discovery_filters_paths_and_reads_only_python_text(
    tmp_path: Path,
) -> None:
    """Discovery keeps tracked .py files and skips untracked or excluded paths."""
    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "tests@example.com")
    _run_git(tmp_path, "config", "user.name", "Context IR Tests")

    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "pkg" / "notes.txt").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "pkg" / "sub").mkdir()
    (tmp_path / "pkg" / "sub" / "b.py").write_text("beta\n", encoding="utf-8")
    for excluded_dir in ("vendor", "vendored", "generated", "build", "cache", ".venv"):
        directory = tmp_path / excluded_dir
        directory.mkdir()
        (directory / "ignored.py").write_text("ignored\n", encoding="utf-8")
    _run_git(
        tmp_path,
        "add",
        "pkg/a.py",
        "pkg/notes.txt",
        "pkg/sub/b.py",
        "vendor/ignored.py",
        "vendored/ignored.py",
        "generated/ignored.py",
        "build/ignored.py",
        "cache/ignored.py",
        ".venv/ignored.py",
    )
    _run_git(tmp_path, "commit", "-m", "base")
    (tmp_path / "pkg" / "untracked.py").write_text("untracked\n", encoding="utf-8")

    file_texts = bm25.discover_real_oss_python_file_texts(tmp_path)

    assert file_texts == (
        bm25.RealOssBaselineFileText("pkg/a.py", "alpha\n"),
        bm25.RealOssBaselineFileText("pkg/sub/b.py", "beta\n"),
    )


def test_dataclass_contracts_are_strict_and_frozen() -> None:
    """Contract dataclasses reject malformed values and cannot be mutated."""
    file_text = bm25.RealOssBaselineFileText("pkg/mod.py", "value\n")
    chunk = bm25.chunk_real_oss_file_text(file_text)[0]

    with pytest.raises(FrozenInstanceError):
        file_text.repo_path = "pkg/other.py"  # type: ignore[misc]
    with pytest.raises(ValueError, match="repository-relative"):
        bm25.RealOssBaselineFileText("/abs/mod.py", "value\n")
    with pytest.raises(ValueError, match="parent traversal"):
        bm25.RealOssBaselineFileText("../mod.py", "value\n")
    with pytest.raises(ValueError, match="end with .py"):
        bm25.RealOssBaselineFileText("pkg/mod.txt", "value\n")
    with pytest.raises(ValueError, match="generated"):
        bm25.RealOssBaselineFileText("vendor/mod.py", "value\n")
    with pytest.raises(ValueError, match="text must be a string"):
        bm25.RealOssBaselineFileText("pkg/mod.py", object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        bm25.RealOssBaselineChunk("pkg/mod.py", 0, 1, "value\n")
    with pytest.raises(ValueError, match="greater than or equal"):
        bm25.RealOssBaselineChunk("pkg/mod.py", 2, 1, "value\n")
    with pytest.raises(ValueError, match="line count"):
        bm25.RealOssBaselineChunk("pkg/mod.py", 1, 2, "value\n")
    with pytest.raises(ValueError, match="non-negative"):
        bm25.RealOssBm25ChunkScore(chunk, -1.0, 1)
    with pytest.raises(ValueError, match="finite"):
        bm25.RealOssBm25ChunkScore(chunk, math.nan, 1)
    with pytest.raises(ValueError, match="token_count"):
        bm25.RealOssBm25ChunkScore(chunk, 0.0, 99)
    with pytest.raises(ValueError, match="query_tokens"):
        bm25.RealOssBm25RetrievalResult("Needle", ("wrong",), ())
    with pytest.raises(ValueError, match="k1"):
        bm25.RealOssBm25RetrievalResult("Needle", ("needle",), (), k1=2.0)


def test_tokenizer_uses_lowercase_unicode_word_tokens_without_filtering() -> None:
    """Tokenization is Unicode word matching, lowercasing, and nothing else."""
    assert bm25.tokenize_real_oss_bm25("The café_runner can't STOP 123") == (
        "the",
        "café_runner",
        "can",
        "t",
        "stop",
        "123",
    )
    assert bm25.tokenize_real_oss_bm25("running runs the") == (
        "running",
        "runs",
        "the",
    )


def test_bm25_ranking_prefers_score_then_path_then_start_line() -> None:
    """Ranking sorts by score descending and then stable chunk identity fields."""
    chunks = (
        _chunk("src/b.py", 1, "needle\n"),
        _chunk("src/a.py", 10, "needle\n"),
        _chunk("src/c.py", 1, "needle needle\n"),
        _chunk("src/a.py", 1, "needle\n"),
    )

    result = bm25.retrieve_real_oss_bm25_chunks(chunks, "needle")

    assert tuple(score.chunk.chunk_id for score in result.chunk_scores) == (
        "src/c.py:1-1",
        "src/a.py:1-1",
        "src/a.py:10-10",
        "src/b.py:1-1",
    )
    assert result.chunk_scores[0].score > result.chunk_scores[1].score
    assert result.chunk_scores[1].score == result.chunk_scores[2].score
    assert result.chunk_scores[2].score == result.chunk_scores[3].score


def test_empty_and_zero_match_queries_return_deterministic_zero_scores() -> None:
    """Empty or no-match queries produce zero scores in path/start order."""
    chunks = (
        _chunk("src/b.py", 1, "alpha\n"),
        _chunk("src/a.py", 10, "beta\n"),
        _chunk("src/a.py", 1, "gamma\n"),
    )

    empty_query_result = bm25.retrieve_real_oss_bm25_chunks(chunks, "")
    missing_query_result = bm25.retrieve_real_oss_bm25_chunks(chunks, "missing")

    assert empty_query_result.query_tokens == ()
    assert tuple(score.score for score in empty_query_result.chunk_scores) == (
        0.0,
        0.0,
        0.0,
    )
    assert tuple(score.chunk.chunk_id for score in empty_query_result.chunk_scores) == (
        "src/a.py:1-1",
        "src/a.py:10-10",
        "src/b.py:1-1",
    )
    assert tuple(score.score for score in missing_query_result.chunk_scores) == (
        0.0,
        0.0,
        0.0,
    )
    assert tuple(
        score.chunk.chunk_id for score in missing_query_result.chunk_scores
    ) == (
        "src/a.py:1-1",
        "src/a.py:10-10",
        "src/b.py:1-1",
    )


def test_contract_has_no_analysis_runtime_or_package_root_surface() -> None:
    """The baseline stays independent of project analysis and API surfaces."""
    source = inspect.getsource(bm25)
    forbidden_source_terms = (
        "context_ir.parser",
        "tree_sitter",
        "analyze_repository",
        "symbol_id",
        "view_id",
        "EvalProviderResult",
        "requests",
        "urllib",
        "httpx",
        "voyage",
        "api_key",
    )

    for forbidden_source_term in forbidden_source_terms:
        assert forbidden_source_term not in source
    assert "RealOssBaselineFileText" not in context_ir.__all__
    assert "RealOssBaselineChunk" not in context_ir.__all__
    assert "RealOssBm25RetrievalResult" not in context_ir.__all__
