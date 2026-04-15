"""Minimal MCP stdio server over the accepted tool facade."""

from __future__ import annotations

from typing import TypeAlias

from mcp.server.fastmcp import FastMCP

import context_ir.tool_facade as tool_facade
from context_ir.semantic_types import (
    ResolverDiagnostic,
    SemanticOptimizationWarning,
    SemanticSelectionRecord,
    SourceSite,
    SourceSpan,
    SyntaxDiagnostic,
    UnresolvedAccess,
    UnsupportedConstruct,
)
from context_ir.tool_facade import SemanticContextRequest, SemanticContextResponse

JsonObject: TypeAlias = dict[str, object]

MCP_SERVER = FastMCP("context-ir")


@MCP_SERVER.tool(
    name="compile_repository_context",
    description="Compile a budgeted semantic context artifact for a repository.",
    structured_output=True,
)
def compile_repository_context(
    repo_root: str,
    query: str,
    budget: int,
    include_document: bool = True,
) -> JsonObject:
    """Compile repository context through the accepted facade for MCP clients."""
    validation_error = _validate_inputs(
        repo_root=repo_root,
        query=query,
        budget=budget,
        include_document=include_document,
    )
    if validation_error is not None:
        return validation_error

    request = SemanticContextRequest(
        repo_root=repo_root,
        query=query,
        budget=budget,
    )
    try:
        response = tool_facade.compile_repository_context(request)
    except Exception as exc:
        return _error("compile_failed", str(exc))

    return _response_to_json(response, include_document=include_document)


def run_stdio_server() -> None:
    """Run the MCP server using stdio transport."""
    MCP_SERVER.run("stdio")


def _validate_inputs(
    *,
    repo_root: str,
    query: str,
    budget: int,
    include_document: bool,
) -> JsonObject | None:
    """Return a JSON-safe validation error or ``None`` for valid inputs."""
    if type(repo_root) is not str or not repo_root:
        return _error("invalid_repo_root", "repo_root must be a non-empty string")
    if type(query) is not str:
        return _error("invalid_query", "query must be a string")
    if type(budget) is not int or budget <= 0:
        return _error("invalid_budget", "budget must be a positive integer")
    if type(include_document) is not bool:
        return _error("invalid_include_document", "include_document must be a boolean")
    return None


def _response_to_json(
    response: SemanticContextResponse,
    *,
    include_document: bool,
) -> JsonObject:
    """Serialize a facade response into JSON-safe primitives."""
    return {
        "ok": True,
        "document": response.compile_result.document if include_document else None,
        "total_tokens": response.compile_total_tokens,
        "budget": response.compile_budget,
        "confidence": response.compile_result.confidence,
        "selected_units": [
            _selection_to_json(selection) for selection in response.selection_trace
        ],
        "omitted_unit_ids": list(response.omitted_unit_ids),
        "unresolved_frontier": [
            _unresolved_access_to_json(access)
            for access in response.unresolved_frontier
        ],
        "unsupported_constructs": [
            _unsupported_construct_to_json(construct)
            for construct in response.unsupported_constructs
        ],
        "syntax_diagnostics": [
            _syntax_diagnostic_to_json(diagnostic)
            for diagnostic in response.syntax_diagnostics
        ],
        "semantic_diagnostics": [
            _resolver_diagnostic_to_json(diagnostic)
            for diagnostic in response.semantic_diagnostics
        ],
        "optimization_warnings": [
            _optimization_warning_to_json(warning)
            for warning in response.optimization_warnings
        ],
    }


def _selection_to_json(selection: SemanticSelectionRecord) -> JsonObject:
    """Serialize one semantic selection trace record."""
    return {
        "unit_id": selection.unit_id,
        "detail": selection.detail,
        "token_count": selection.token_count,
        "basis": selection.basis.value,
        "reason": selection.reason,
        "edit_score": selection.edit_score,
        "support_score": selection.support_score,
    }


def _unresolved_access_to_json(access: UnresolvedAccess) -> JsonObject:
    """Serialize one unresolved semantic frontier item."""
    return {
        "access_id": access.access_id,
        "site": _source_site_to_json(access.site),
        "access_text": access.access_text,
        "context": access.context.value,
        "enclosing_scope_id": access.enclosing_scope_id,
        "reason_code": access.reason_code.value,
        "detail": access.detail,
        "proof_status": access.proof_status.value,
    }


def _unsupported_construct_to_json(construct: UnsupportedConstruct) -> JsonObject:
    """Serialize one unsupported semantic construct."""
    return {
        "construct_id": construct.construct_id,
        "site": _source_site_to_json(construct.site),
        "construct_text": construct.construct_text,
        "reason_code": construct.reason_code.value,
        "detail": construct.detail,
        "enclosing_scope_id": construct.enclosing_scope_id,
        "proof_status": construct.proof_status.value,
    }


def _syntax_diagnostic_to_json(diagnostic: SyntaxDiagnostic) -> JsonObject:
    """Serialize one syntax diagnostic."""
    return {
        "diagnostic_id": diagnostic.diagnostic_id,
        "file_id": diagnostic.file_id,
        "site": _source_site_to_json(diagnostic.site),
        "code": diagnostic.code.value,
        "message": diagnostic.message,
    }


def _resolver_diagnostic_to_json(diagnostic: ResolverDiagnostic) -> JsonObject:
    """Serialize one semantic resolver diagnostic."""
    return {
        "diagnostic_id": diagnostic.diagnostic_id,
        "site": _source_site_to_json(diagnostic.site),
        "severity": diagnostic.severity.value,
        "reason_code": diagnostic.reason_code.value,
        "message": diagnostic.message,
        "related_symbol_id": diagnostic.related_symbol_id,
    }


def _optimization_warning_to_json(
    warning: SemanticOptimizationWarning,
) -> JsonObject:
    """Serialize one optimization warning."""
    return {
        "code": warning.code.value,
        "message": warning.message,
        "unit_id": warning.unit_id,
    }


def _source_site_to_json(site: SourceSite) -> JsonObject:
    """Serialize stable source-site fields only."""
    return {
        "site_id": site.site_id,
        "file_path": site.file_path,
        "span": _source_span_to_json(site.span),
    }


def _source_span_to_json(span: SourceSpan) -> JsonObject:
    """Serialize a source span into stable numeric fields."""
    return {
        "start_line": span.start_line,
        "start_column": span.start_column,
        "end_line": span.end_line,
        "end_column": span.end_column,
    }


def _error(code: str, message: str) -> JsonObject:
    """Return a JSON-safe error response."""
    return {
        "ok": False,
        "error": message,
        "error_code": code,
    }


if __name__ == "__main__":
    run_stdio_server()


__all__ = [
    "MCP_SERVER",
    "compile_repository_context",
    "run_stdio_server",
]
