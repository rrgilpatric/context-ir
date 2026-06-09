"""Internal real-OSS BM25 chunking and retrieval contracts."""

from __future__ import annotations

import math
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REAL_OSS_BM25_CHUNK_TARGET_LINES = 160
REAL_OSS_BM25_CHUNK_OVERLAP_LINES = 40
REAL_OSS_BM25_K1 = 1.2
REAL_OSS_BM25_B = 0.75

_TOKEN_PATTERN = re.compile(r"\w+")
_EXCLUDED_PATH_PARTS = frozenset(
    {
        ".cache",
        ".eggs",
        ".git",
        ".hg",
        ".hypothesis",
        ".ipynb_checkpoints",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "cache",
        "dist",
        "eggs",
        "env",
        "generated",
        "node_modules",
        "site-packages",
        "vendor",
        "vendored",
        "venv",
    }
)


@dataclass(frozen=True)
class RealOssBaselineFileText:
    """Raw repository text for one eligible Python file."""

    repo_path: str
    text: str

    def __post_init__(self) -> None:
        """Reject malformed baseline file text contracts."""
        _validate_repo_python_path(self.repo_path, field_name="repo_path")
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")

    @property
    def file_id(self) -> str:
        """Return the stable raw-file identity."""
        return self.repo_path


@dataclass(frozen=True)
class RealOssBaselineChunk:
    """Raw text chunk identified only by repository path and line range."""

    repo_path: str
    start_line: int
    end_line: int
    text: str

    def __post_init__(self) -> None:
        """Reject malformed chunk identity, range, or text payloads."""
        _validate_repo_python_path(self.repo_path, field_name="repo_path")
        _validate_positive_int(self.start_line, field_name="start_line")
        _validate_positive_int(self.end_line, field_name="end_line")
        if self.end_line < self.start_line:
            raise ValueError("end_line must be greater than or equal to start_line")
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        if not self.text:
            raise ValueError("text must be non-empty")
        if _content_line_count(self.text) != self.line_count:
            raise ValueError("text line count must match start_line/end_line")

    @property
    def chunk_id(self) -> str:
        """Return the stable chunk identity."""
        return f"{self.repo_path}:{self.start_line}-{self.end_line}"

    @property
    def line_count(self) -> int:
        """Return the inclusive line count covered by this chunk."""
        return self.end_line - self.start_line + 1


@dataclass(frozen=True)
class RealOssBm25ChunkScore:
    """BM25 score metadata for one baseline chunk."""

    chunk: RealOssBaselineChunk
    score: float
    token_count: int

    def __post_init__(self) -> None:
        """Reject malformed score records."""
        if not isinstance(self.chunk, RealOssBaselineChunk):
            raise ValueError("chunk must be a RealOssBaselineChunk")
        if isinstance(self.score, bool) or not isinstance(self.score, int | float):
            raise ValueError("score must be a finite number")
        if not math.isfinite(self.score):
            raise ValueError("score must be finite")
        if self.score < 0:
            raise ValueError("score must be non-negative")
        if isinstance(self.token_count, bool) or not isinstance(self.token_count, int):
            raise ValueError("token_count must be an integer")
        if self.token_count < 0:
            raise ValueError("token_count must be non-negative")
        if self.token_count != len(tokenize_real_oss_bm25(self.chunk.text)):
            raise ValueError("token_count must match chunk text tokenization")


@dataclass(frozen=True)
class RealOssBm25RetrievalResult:
    """Deterministic BM25 retrieval result for a raw chunk set."""

    query: str
    query_tokens: tuple[str, ...]
    chunk_scores: tuple[RealOssBm25ChunkScore, ...]
    k1: float = REAL_OSS_BM25_K1
    b: float = REAL_OSS_BM25_B

    def __post_init__(self) -> None:
        """Reject result records that drift from the frozen BM25 contract."""
        if not isinstance(self.query, str):
            raise ValueError("query must be a string")
        _validate_string_tuple(self.query_tokens, field_name="query_tokens")
        if self.query_tokens != tokenize_real_oss_bm25(self.query):
            raise ValueError("query_tokens must match frozen BM25 tokenization")
        if not isinstance(self.chunk_scores, tuple):
            raise ValueError("chunk_scores must be a tuple")
        if any(
            not isinstance(chunk_score, RealOssBm25ChunkScore)
            for chunk_score in self.chunk_scores
        ):
            raise ValueError("chunk_scores must contain RealOssBm25ChunkScore values")
        if self.k1 != REAL_OSS_BM25_K1:
            raise ValueError("k1 must match the frozen BM25 contract")
        if self.b != REAL_OSS_BM25_B:
            raise ValueError("b must match the frozen BM25 contract")
        if self.chunk_scores != tuple(
            sorted(self.chunk_scores, key=_chunk_score_sort_key)
        ):
            raise ValueError("chunk_scores must be sorted by frozen BM25 ordering")
        _reject_duplicate_chunk_scores(self.chunk_scores)


def discover_real_oss_python_file_texts(
    repo_root: Path | str,
) -> tuple[RealOssBaselineFileText, ...]:
    """Return eligible tracked Python file text records in repository path order."""
    root = Path(repo_root)
    if not root.exists():
        raise ValueError("repo_root must exist")
    if not root.is_dir():
        raise ValueError("repo_root must be a directory")

    files: list[RealOssBaselineFileText] = []
    for repo_path in _git_tracked_python_paths(root):
        path = root / repo_path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(
                f"unable to read tracked Python file {repo_path}"
            ) from error
        files.append(
            RealOssBaselineFileText(
                repo_path=repo_path,
                text=text,
            )
        )
    return tuple(files)


def chunk_real_oss_file_text(
    file_text: RealOssBaselineFileText,
) -> tuple[RealOssBaselineChunk, ...]:
    """Split one raw Python file into frozen overlapping baseline chunks."""
    if not isinstance(file_text, RealOssBaselineFileText):
        raise ValueError("file_text must be a RealOssBaselineFileText")

    lines = tuple(file_text.text.splitlines(keepends=True))
    if not lines:
        return ()

    chunks: list[RealOssBaselineChunk] = []
    step = REAL_OSS_BM25_CHUNK_TARGET_LINES - REAL_OSS_BM25_CHUNK_OVERLAP_LINES
    start_index = 0
    while start_index < len(lines):
        end_index = min(start_index + REAL_OSS_BM25_CHUNK_TARGET_LINES, len(lines))
        chunks.append(
            RealOssBaselineChunk(
                repo_path=file_text.repo_path,
                start_line=start_index + 1,
                end_line=end_index,
                text="".join(lines[start_index:end_index]),
            )
        )
        if end_index == len(lines):
            break
        start_index += step

    return tuple(chunks)


def chunk_real_oss_file_texts(
    file_texts: tuple[RealOssBaselineFileText, ...],
) -> tuple[RealOssBaselineChunk, ...]:
    """Split raw Python files into reusable baseline chunks in stable order."""
    if not isinstance(file_texts, tuple):
        raise ValueError("file_texts must be a tuple")
    if any(
        not isinstance(file_text, RealOssBaselineFileText) for file_text in file_texts
    ):
        raise ValueError("file_texts must contain RealOssBaselineFileText values")
    _reject_duplicate_file_texts(file_texts)

    chunks: list[RealOssBaselineChunk] = []
    for file_text in sorted(file_texts, key=lambda record: record.repo_path):
        chunks.extend(chunk_real_oss_file_text(file_text))
    return tuple(chunks)


def build_real_oss_baseline_chunks(
    repo_root: Path | str,
) -> tuple[RealOssBaselineChunk, ...]:
    """Discover tracked Python files and return frozen raw-text baseline chunks."""
    return chunk_real_oss_file_texts(discover_real_oss_python_file_texts(repo_root))


def tokenize_real_oss_bm25(text: str) -> tuple[str, ...]:
    """Return lowercase Unicode word tokens for the frozen BM25 contract."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return tuple(match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text))


def retrieve_real_oss_bm25_chunks(
    chunks: tuple[RealOssBaselineChunk, ...],
    query: str,
) -> RealOssBm25RetrievalResult:
    """Score and rank baseline chunks with the frozen BM25 parameters."""
    if not isinstance(chunks, tuple):
        raise ValueError("chunks must be a tuple")
    if any(not isinstance(chunk, RealOssBaselineChunk) for chunk in chunks):
        raise ValueError("chunks must contain RealOssBaselineChunk values")
    if not isinstance(query, str):
        raise ValueError("query must be a string")
    _reject_duplicate_chunks(chunks)

    query_tokens = tokenize_real_oss_bm25(query)
    query_terms = _unique_ordered_tokens(query_tokens)
    chunk_term_counts = tuple(
        Counter(tokenize_real_oss_bm25(chunk.text)) for chunk in chunks
    )
    document_lengths = tuple(
        sum(term_counts.values()) for term_counts in chunk_term_counts
    )
    document_frequencies: Counter[str] = Counter()
    for term_counts in chunk_term_counts:
        for term in term_counts:
            document_frequencies[term] += 1

    document_count = len(chunks)
    average_document_length = (
        sum(document_lengths) / document_count if document_count else 0.0
    )
    chunk_scores = tuple(
        _score_chunk(
            chunk=chunk,
            query_terms=query_terms,
            term_counts=term_counts,
            document_frequencies=document_frequencies,
            document_count=document_count,
            document_length=document_length,
            average_document_length=average_document_length,
        )
        for chunk, term_counts, document_length in zip(
            chunks,
            chunk_term_counts,
            document_lengths,
            strict=True,
        )
    )
    return RealOssBm25RetrievalResult(
        query=query,
        query_tokens=query_tokens,
        chunk_scores=tuple(sorted(chunk_scores, key=_chunk_score_sort_key)),
    )


def retrieve_real_oss_bm25_from_repo(
    repo_root: Path | str,
    query: str,
) -> RealOssBm25RetrievalResult:
    """Discover, chunk, score, and rank tracked repository Python text."""
    return retrieve_real_oss_bm25_chunks(
        build_real_oss_baseline_chunks(repo_root),
        query,
    )


def _git_tracked_python_paths(repo_root: Path) -> tuple[str, ...]:
    """Return eligible tracked Python paths from the checked-out repository."""
    try:
        completed_process = subprocess.run(
            ("git", "-C", str(repo_root), "ls-files", "-z", "--", "*.py"),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise ValueError("unable to list tracked Python files") from error

    if completed_process.returncode != 0:
        detail = completed_process.stderr.strip()
        if detail:
            raise ValueError(f"unable to list tracked Python files: {detail}")
        raise ValueError("unable to list tracked Python files")

    return tuple(
        sorted(
            repo_path
            for repo_path in completed_process.stdout.split("\0")
            if repo_path and _is_eligible_repo_python_path(repo_path)
        )
    )


def _is_eligible_repo_python_path(repo_path: str) -> bool:
    """Return whether a tracked path passes the frozen baseline path rules."""
    try:
        _validate_repo_python_path(repo_path, field_name="repo_path")
    except ValueError:
        return False
    return True


def _score_chunk(
    *,
    chunk: RealOssBaselineChunk,
    query_terms: tuple[str, ...],
    term_counts: Counter[str],
    document_frequencies: Counter[str],
    document_count: int,
    document_length: int,
    average_document_length: float,
) -> RealOssBm25ChunkScore:
    """Return a BM25 score record for one chunk."""
    score = 0.0
    for term in query_terms:
        term_frequency = term_counts[term]
        document_frequency = document_frequencies[term]
        if term_frequency == 0 or document_frequency == 0:
            continue
        score += _bm25_term_score(
            term_frequency=term_frequency,
            document_frequency=document_frequency,
            document_count=document_count,
            document_length=document_length,
            average_document_length=average_document_length,
        )
    return RealOssBm25ChunkScore(
        chunk=chunk,
        score=score,
        token_count=document_length,
    )


def _bm25_term_score(
    *,
    term_frequency: int,
    document_frequency: int,
    document_count: int,
    document_length: int,
    average_document_length: float,
) -> float:
    """Return the BM25 contribution for one query term and chunk."""
    idf = math.log(
        1.0 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
    )
    length_ratio = (
        document_length / average_document_length
        if average_document_length > 0.0
        else 0.0
    )
    length_normalization = 1.0 - REAL_OSS_BM25_B + REAL_OSS_BM25_B * length_ratio
    denominator = term_frequency + REAL_OSS_BM25_K1 * length_normalization
    return idf * (term_frequency * (REAL_OSS_BM25_K1 + 1.0)) / denominator


def _chunk_score_sort_key(
    chunk_score: RealOssBm25ChunkScore,
) -> tuple[float, str, int]:
    """Return the frozen deterministic ranking key."""
    return (
        -chunk_score.score,
        chunk_score.chunk.repo_path,
        chunk_score.chunk.start_line,
    )


def _validate_repo_python_path(repo_path: str, *, field_name: str) -> None:
    """Reject paths outside the frozen raw Python file contract."""
    if not isinstance(repo_path, str):
        raise ValueError(f"{field_name} must be a string")
    if not repo_path:
        raise ValueError(f"{field_name} must be non-empty")
    if "\\" in repo_path:
        raise ValueError(f"{field_name} must use POSIX separators")

    posix_path = PurePosixPath(repo_path)
    if posix_path.as_posix() != repo_path:
        raise ValueError(f"{field_name} must be a normalized POSIX path")
    if posix_path.is_absolute():
        raise ValueError(f"{field_name} must be repository-relative")
    if ".." in posix_path.parts:
        raise ValueError(f"{field_name} must not contain parent traversal")
    if posix_path.suffix != ".py":
        raise ValueError(f"{field_name} must end with .py")
    if _EXCLUDED_PATH_PARTS & frozenset(posix_path.parts):
        raise ValueError(
            f"{field_name} must not be generated, vendored, cached, or virtualenv"
        )


def _validate_positive_int(value: int, *, field_name: str) -> None:
    """Reject non-integer and non-positive values."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_string_tuple(value: tuple[str, ...], *, field_name: str) -> None:
    """Reject non-tuple or non-string token payloads."""
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must contain strings")


def _content_line_count(text: str) -> int:
    """Return the count of content lines represented by raw text."""
    return len(text.splitlines(keepends=True))


def _unique_ordered_tokens(tokens: tuple[str, ...]) -> tuple[str, ...]:
    """Return first-seen unique tokens without changing token text."""
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique_tokens.append(token)
    return tuple(unique_tokens)


def _reject_duplicate_file_texts(
    file_texts: tuple[RealOssBaselineFileText, ...],
) -> None:
    """Reject duplicate file text identities before chunking."""
    seen_paths: set[str] = set()
    for file_text in file_texts:
        if file_text.repo_path in seen_paths:
            raise ValueError("duplicate repo_path in file_texts")
        seen_paths.add(file_text.repo_path)


def _reject_duplicate_chunks(chunks: tuple[RealOssBaselineChunk, ...]) -> None:
    """Reject duplicate chunk identities before scoring."""
    seen_chunk_ids: set[str] = set()
    for chunk in chunks:
        if chunk.chunk_id in seen_chunk_ids:
            raise ValueError("duplicate chunk identity")
        seen_chunk_ids.add(chunk.chunk_id)


def _reject_duplicate_chunk_scores(
    chunk_scores: tuple[RealOssBm25ChunkScore, ...],
) -> None:
    """Reject duplicate chunk identities in retrieval results."""
    _reject_duplicate_chunks(tuple(chunk_score.chunk for chunk_score in chunk_scores))
