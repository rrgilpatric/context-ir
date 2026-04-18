"""Tool-facing facade tests for semantic repository compilation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import context_ir
import context_ir.compiler as legacy_compiler
import context_ir.optimizer as legacy_optimizer
import context_ir.parser as legacy_parser
import context_ir.renderer as legacy_renderer
import context_ir.scorer as legacy_scorer
import context_ir.semantic_types as semantic_types
import context_ir.tool_facade as tool_facade
from context_ir.semantic_types import (
    ReferenceContext,
    SelectionBasis,
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticSelectionRecord,
    SyntaxDiagnosticCode,
    SyntaxProgram,
    UnresolvedReasonCode,
)
from context_ir.tool_facade import (
    SemanticContextRequest,
    SemanticContextResponse,
    compile_repository_context,
)


def _estimate_tokens(text: str) -> int:
    """Mirror compile-level token estimation for assembled documents."""
    return max(1, (len(text) + 3) // 4)


def test_compile_repository_context_returns_typed_response_for_simple_repo(
    tmp_path: Path,
) -> None:
    """The facade returns the semantic program and compile result together."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run helper",
            budget=1000,
        )
    )

    assert isinstance(response, SemanticContextResponse)
    assert isinstance(response.program, SemanticProgram)
    assert isinstance(response.compile_result, SemanticCompileResult)
    assert response.program.repo_root == tmp_path
    assert response.compile_result.compile_context == SemanticCompileContext(
        query="run helper"
    )
    assert response.compile_budget == 1000
    assert response.compile_total_tokens == response.compile_result.total_tokens


def test_compile_repository_context_uses_analyzer_and_semantic_compiler(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade delegates to accepted analyzer and semantic compiler APIs."""
    calls: list[str] = []
    syntax = SyntaxProgram(repo_root=tmp_path)
    program = SemanticProgram(repo_root=tmp_path, syntax=syntax)
    selection = SemanticSelectionRecord(
        unit_id="unit:one",
        detail="identity",
        token_count=0,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="fake trace",
        edit_score=0.1,
        support_score=0.0,
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.BUDGET_PRESSURE,
        message="fake warning",
        unit_id="unit:one",
    )
    optimization = SemanticOptimizationResult(
        selections=(selection,),
        omitted_unit_ids=("unit:two",),
        warnings=(warning,),
        total_tokens=0,
        budget=64,
        confidence=0.5,
    )
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nfake",
        optimization=optimization,
        omitted_unit_ids=("unit:two",),
        total_tokens=6,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )

    def injected_embed(texts: list[str]) -> list[list[float]]:
        """Return deterministic vectors for pass-through verification."""
        return [[0.0] for _ in texts]

    def fake_analyze(repo_root: Path | str) -> SemanticProgram:
        calls.append(f"analyze:{repo_root}")
        return program

    def fake_compile(
        received_program: SemanticProgram,
        query: str,
        budget: int,
        *,
        embed_fn: tool_facade.EmbeddingFunction | None = None,
    ) -> SemanticCompileResult:
        calls.append(f"compile:{query}:{budget}")
        assert received_program is program
        assert embed_fn is injected_embed
        return compile_result

    monkeypatch.setattr(tool_facade, "analyze_repository", fake_analyze)
    monkeypatch.setattr(tool_facade, "compile_semantic_context", fake_compile)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=str(tmp_path),
            query="query",
            budget=64,
            embed_fn=injected_embed,
        )
    )

    assert response.program is program
    assert response.compile_result is compile_result
    assert response.selection_trace == (selection,)
    assert response.optimization_warnings == (warning,)
    assert response.omitted_unit_ids == ("unit:two",)
    assert calls == [f"analyze:{tmp_path}", "compile:query:64"]


def test_compile_repository_context_exposes_uncertainty_and_unsupported_constructs(
    tmp_path: Path,
) -> None:
    """Frontier and unsupported lower-layer surfaces remain explicit."""
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "helpers.py").write_text(
        "def helper() -> None:\n    return None\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            from pkg.helpers import *
            from pkg.helpers import helper

            def run() -> None:
                helper()
                missing_call()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run missing_call from pkg.helpers import *",
            budget=1000,
        )
    )

    assert response.unresolved_frontier == tuple(response.program.unresolved_frontier)
    assert response.unsupported_constructs == tuple(
        response.program.unsupported_constructs
    )
    assert any(
        access.access_text == "missing_call"
        and access.context is ReferenceContext.CALL
        and access.reason_code is UnresolvedReasonCode.UNRESOLVED_NAME
        for access in response.unresolved_frontier
    )
    assert any(
        construct.construct_text == "from pkg.helpers import *"
        and construct.reason_code is UnresolvedReasonCode.STAR_IMPORT
        for construct in response.unsupported_constructs
    )
    assert "unresolved:" in response.compile_result.document
    assert "unsupported construct" in response.compile_result.document
    assert "text: from pkg.helpers import *" in response.compile_result.document


def test_compile_repository_context_preserves_parse_error_truthfulness(
    tmp_path: Path,
) -> None:
    """Parse-error files stay visible without gaining semantic facts."""
    (tmp_path / "good.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text(
        "from good import VALUE\nclass Broken(\n",
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="VALUE",
            budget=1000,
        )
    )

    assert response.syntax_diagnostics == tuple(response.program.syntax.diagnostics)
    assert {"file:good.py", "file:bad.py"}.issubset(
        response.program.syntax.source_files
    )
    assert any(
        diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
        and diagnostic.file_id == "file:bad.py"
        for diagnostic in response.syntax_diagnostics
    )
    assert all(
        symbol.file_id != "file:bad.py"
        for symbol in response.program.resolved_symbols.values()
    )
    assert all(
        binding.site.file_path != "bad.py" for binding in response.program.bindings
    )
    assert all(
        reference.site.file_path != "bad.py"
        for reference in response.program.resolved_references
    )
    assert all(
        access.site.file_path != "bad.py" for access in response.unresolved_frontier
    )
    assert all(
        construct.site.file_path != "bad.py"
        for construct in response.unsupported_constructs
    )


def test_compile_repository_context_preserves_budget_honesty(
    tmp_path: Path,
) -> None:
    """Facade totals mirror the underlying compile result and requested budget."""
    (tmp_path / "main.py").write_text(
        textwrap.dedent(
            """
            def helper() -> None:
                return None

            def run() -> None:
                helper()
            """
        ).lstrip(),
        encoding="utf-8",
    )

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run",
            budget=200,
        )
    )

    assert response.compile_budget == response.compile_result.budget == 200
    assert response.compile_total_tokens == response.compile_result.total_tokens
    assert response.compile_total_tokens == _estimate_tokens(
        response.compile_result.document
    )
    assert response.compile_total_tokens <= response.compile_budget
    assert (
        response.compile_result.optimization.total_tokens
        <= response.compile_total_tokens
    )


def test_compile_repository_context_does_not_call_retired_graph_first_apis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The facade does not route through retired graph-first entry points."""
    (tmp_path / "main.py").write_text(
        "def run() -> None:\n    return None\n",
        encoding="utf-8",
    )

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("retired graph-first API was called")

    monkeypatch.setattr(legacy_parser, "parse_file", fail)
    monkeypatch.setattr(legacy_parser, "parse_repository", fail)
    monkeypatch.setattr(legacy_scorer, "score_graph", fail)
    monkeypatch.setattr(legacy_optimizer, "optimize", fail)
    monkeypatch.setattr(legacy_renderer, "render", fail)
    monkeypatch.setattr(legacy_compiler, "compile", fail)

    response = compile_repository_context(
        SemanticContextRequest(
            repo_root=tmp_path,
            query="run",
            budget=200,
        )
    )

    assert isinstance(response, SemanticContextResponse)


def test_tool_facade_does_not_change_package_root_exports() -> None:
    """The facade remains an explicit module API rather than a root export."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)

    facade_names = {
        "EmbeddingFunction",
        "SemanticContextRequest",
        "SemanticContextResponse",
        "compile_repository_context",
    }

    assert facade_names.isdisjoint(context_ir.__all__)
    assert not hasattr(context_ir, "SemanticContextRequest")
    assert not hasattr(context_ir, "SemanticContextResponse")
    assert not hasattr(context_ir, "compile_repository_context")
