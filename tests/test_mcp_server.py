"""Tests for the minimal MCP wrapper over the tool facade."""

from __future__ import annotations

import asyncio
import textwrap
from pathlib import Path

import context_ir
import context_ir.compiler as legacy_compiler
import context_ir.mcp_server as mcp_server
import context_ir.optimizer as legacy_optimizer
import context_ir.parser as legacy_parser
import context_ir.renderer as legacy_renderer
import context_ir.scorer as legacy_scorer
import context_ir.semantic_types as semantic_types
from context_ir.semantic_types import (
    DiagnosticSeverity,
    ReferenceContext,
    ResolverDiagnostic,
    SelectionBasis,
    SemanticCompileContext,
    SemanticCompileResult,
    SemanticOptimizationResult,
    SemanticOptimizationWarning,
    SemanticOptimizationWarningCode,
    SemanticProgram,
    SemanticSelectionRecord,
    SourceSite,
    SourceSpan,
    SyntaxDiagnostic,
    SyntaxDiagnosticCode,
    SyntaxProgram,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)
from context_ir.tool_facade import (
    SemanticContextRequest,
    SemanticContextResponse,
)


def test_mcp_tool_delegates_to_tool_facade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The MCP tool builds a facade request and calls the accepted facade."""
    calls: list[SemanticContextRequest] = []

    def fake_compile_repository_context(
        request: SemanticContextRequest,
    ) -> SemanticContextResponse:
        calls.append(request)
        return _fake_response(tmp_path)

    monkeypatch.setattr(
        mcp_server.tool_facade,
        "compile_repository_context",
        fake_compile_repository_context,
    )

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="find run",
        budget=64,
    )

    assert calls == [
        SemanticContextRequest(
            repo_root=str(tmp_path),
            query="find run",
            budget=64,
        )
    ]
    assert result["ok"] is True
    assert result["document"] == "# Semantic Context\nfake document"


def test_mcp_tool_output_is_json_safe_and_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The serialized MCP result contains JSON-safe facade surfaces."""
    monkeypatch.setattr(
        mcp_server.tool_facade,
        "compile_repository_context",
        lambda request: _fake_response(tmp_path),
    )

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="query",
        budget=64,
    )

    assert set(result) == {
        "ok",
        "document",
        "total_tokens",
        "budget",
        "confidence",
        "selected_units",
        "omitted_unit_ids",
        "unresolved_frontier",
        "unsupported_constructs",
        "syntax_diagnostics",
        "semantic_diagnostics",
        "optimization_warnings",
    }
    assert result["ok"] is True
    assert result["document"] == "# Semantic Context\nfake document"
    assert result["budget"] == 64
    assert result["total_tokens"] == 12
    assert result["confidence"] == 0.5
    assert result["selected_units"] == [
        {
            "unit_id": "unit:one",
            "detail": "summary",
            "token_count": 4,
            "basis": "heuristic_candidate",
            "reason": "selected for query",
            "edit_score": 0.7,
            "support_score": 0.2,
        }
    ]
    assert result["omitted_unit_ids"] == ["unit:two"]
    _assert_json_safe(result)


def test_include_document_false_preserves_trace_uncertainty_and_diagnostics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Document omission does not hide trace, uncertainty, or warnings."""
    monkeypatch.setattr(
        mcp_server.tool_facade,
        "compile_repository_context",
        lambda request: _fake_response(tmp_path),
    )

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="query",
        budget=64,
        include_document=False,
    )

    assert result["ok"] is True
    assert result["document"] is None
    assert result["selected_units"]
    assert result["omitted_unit_ids"] == ["unit:two"]
    assert result["unresolved_frontier"]
    assert result["unsupported_constructs"]
    assert result["syntax_diagnostics"]
    assert result["semantic_diagnostics"]
    assert result["optimization_warnings"]
    _assert_json_safe(result)


def test_unresolved_frontier_and_unsupported_constructs_remain_explicit(
    tmp_path: Path,
) -> None:
    """Real analyzer uncertainty surfaces remain visible through MCP JSON."""
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

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="run missing_call from pkg.helpers import *",
        budget=1000,
    )

    assert result["ok"] is True
    unresolved_frontier = result["unresolved_frontier"]
    unsupported_constructs = result["unsupported_constructs"]
    assert isinstance(unresolved_frontier, list)
    assert isinstance(unsupported_constructs, list)
    assert any(
        access["access_text"] == "missing_call"
        and access["reason_code"] == "unresolved_name"
        and access["proof_status"] == "unknown"
        for access in unresolved_frontier
        if isinstance(access, dict)
    )
    assert any(
        construct["construct_text"] == "from pkg.helpers import *"
        and construct["reason_code"] == "star_import"
        and construct["proof_status"] == "unsupported"
        for construct in unsupported_constructs
        if isinstance(construct, dict)
    )


def test_parse_error_diagnostics_remain_visible(tmp_path: Path) -> None:
    """Syntax parse errors are preserved in MCP output."""
    (tmp_path / "good.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text(
        "from good import VALUE\nclass Broken(\n",
        encoding="utf-8",
    )

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="VALUE",
        budget=1000,
    )

    assert result["ok"] is True
    diagnostics = result["syntax_diagnostics"]
    assert isinstance(diagnostics, list)
    assert any(
        diagnostic["code"] == "parse_error" and diagnostic["file_id"] == "file:bad.py"
        for diagnostic in diagnostics
        if isinstance(diagnostic, dict)
    )


def test_invalid_budget_returns_json_safe_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Non-positive budgets are rejected before facade delegation."""
    calls = 0

    def fail_if_called(request: SemanticContextRequest) -> SemanticContextResponse:
        nonlocal calls
        calls += 1
        raise AssertionError("facade should not be called for invalid budget")

    monkeypatch.setattr(
        mcp_server.tool_facade,
        "compile_repository_context",
        fail_if_called,
    )

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="query",
        budget=0,
    )

    assert result == {
        "ok": False,
        "error": "budget must be a positive integer",
        "error_code": "invalid_budget",
    }
    assert calls == 0
    _assert_json_safe(result)


def test_mcp_tool_does_not_call_retired_graph_first_apis(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The MCP wrapper routes through the semantic facade, not legacy APIs."""
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

    result = mcp_server.compile_repository_context(
        repo_root=str(tmp_path),
        query="run",
        budget=200,
    )

    assert result["ok"] is True


def test_mcp_server_registers_exactly_one_compile_tool(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """The official SDK registration and local invocation are covered."""
    monkeypatch.setattr(
        mcp_server.tool_facade,
        "compile_repository_context",
        lambda request: _fake_response(tmp_path),
    )

    tools = asyncio.run(mcp_server.MCP_SERVER.list_tools())
    assert [tool.name for tool in tools] == ["compile_repository_context"]

    result = asyncio.run(
        mcp_server.MCP_SERVER.call_tool(
            "compile_repository_context",
            {
                "repo_root": str(tmp_path),
                "query": "query",
                "budget": 64,
                "include_document": False,
            },
        )
    )

    assert isinstance(result, tuple)
    _content, structured_result = result
    assert isinstance(structured_result, dict)
    assert structured_result["ok"] is True
    assert structured_result["document"] is None
    _assert_json_safe(structured_result)


def test_mcp_server_does_not_change_package_root_exports() -> None:
    """The MCP surface stays out of package-root exports."""
    assert tuple(context_ir.__all__) == tuple(semantic_types.__all__)
    assert "MCP_SERVER" not in context_ir.__all__
    assert "compile_repository_context" not in context_ir.__all__
    assert not hasattr(context_ir, "MCP_SERVER")
    assert not hasattr(context_ir, "compile_repository_context")


def _fake_response(repo_root: Path) -> SemanticContextResponse:
    """Build a facade response with every MCP-facing surface populated."""
    site = SourceSite(
        site_id="site:main:1",
        file_path="main.py",
        span=SourceSpan(
            start_line=1,
            start_column=0,
            end_line=1,
            end_column=10,
        ),
        snippet="unstable snippet omitted by serializer",
    )
    syntax_diagnostic = SyntaxDiagnostic(
        diagnostic_id="syntax:bad",
        file_id="file:bad.py",
        site=site,
        code=SyntaxDiagnosticCode.PARSE_ERROR,
        message="could not parse file",
    )
    unresolved = UnresolvedAccess(
        access_id="frontier:missing",
        site=site,
        access_text="missing_call",
        context=ReferenceContext.CALL,
        enclosing_scope_id="scope:main",
        reason_code=UnresolvedReasonCode.UNRESOLVED_NAME,
        detail="not found in supported scope",
    )
    unsupported = UnsupportedConstruct(
        construct_id="unsupported:star",
        site=site,
        construct_text="from pkg.helpers import *",
        reason_code=UnresolvedReasonCode.STAR_IMPORT,
        detail="star imports are unsupported",
        enclosing_scope_id="scope:main",
    )
    semantic_diagnostic = ResolverDiagnostic(
        diagnostic_id="semantic:missing",
        site=site,
        severity=DiagnosticSeverity.WARNING,
        reason_code=UnresolvedReasonCode.UNRESOLVED_NAME,
        message="could not resolve missing_call",
        related_symbol_id=None,
    )
    selection = SemanticSelectionRecord(
        unit_id="unit:one",
        detail="summary",
        token_count=4,
        basis=SelectionBasis.HEURISTIC_CANDIDATE,
        reason="selected for query",
        edit_score=0.7,
        support_score=0.2,
    )
    warning = SemanticOptimizationWarning(
        code=SemanticOptimizationWarningCode.OMITTED_UNCERTAINTY,
        message="uncertainty omitted by budget",
        unit_id="frontier:missing",
    )
    optimization = SemanticOptimizationResult(
        selections=(selection,),
        omitted_unit_ids=("unit:two",),
        warnings=(warning,),
        total_tokens=4,
        budget=64,
        confidence=0.5,
    )
    compile_result = SemanticCompileResult(
        document="# Semantic Context\nfake document",
        optimization=optimization,
        omitted_unit_ids=("unit:two",),
        total_tokens=12,
        budget=64,
        confidence=0.5,
        compile_context=SemanticCompileContext(query="query"),
    )
    syntax = SyntaxProgram(
        repo_root=repo_root,
        diagnostics=[syntax_diagnostic],
    )
    program = SemanticProgram(
        repo_root=repo_root,
        syntax=syntax,
        unresolved_frontier=[unresolved],
        unsupported_constructs=[unsupported],
        diagnostics=[semantic_diagnostic],
    )
    return SemanticContextResponse(
        program=program,
        compile_result=compile_result,
        unresolved_frontier=tuple(program.unresolved_frontier),
        unsupported_constructs=tuple(program.unsupported_constructs),
        syntax_diagnostics=tuple(program.syntax.diagnostics),
        semantic_diagnostics=tuple(program.diagnostics),
        optimization_warnings=compile_result.optimization.warnings,
        selection_trace=compile_result.optimization.selections,
        omitted_unit_ids=compile_result.omitted_unit_ids,
        compile_total_tokens=compile_result.total_tokens,
        compile_budget=compile_result.budget,
    )


def _assert_json_safe(value: object) -> None:
    """Assert that a value is composed only of JSON-safe primitives."""
    if value is None or type(value) in {str, int, float, bool}:
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_safe(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            assert isinstance(key, str)
            _assert_json_safe(item)
        return
    raise AssertionError(f"non JSON-safe value: {value!r}")
