"""Semantic dependency and frontier derivation for the semantic-first baseline."""

from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass

from context_ir.semantic_types import (
    BaseExpressionFact,
    DecoratorFact,
    DecoratorSupport,
    DependencyProofKind,
    ImportFact,
    ImportKind,
    ImportTargetKind,
    RawDefinitionFact,
    ReferenceContext,
    ResolvedImport,
    ResolvedReference,
    ResolvedSymbol,
    ResolvedSymbolKind,
    SemanticDependency,
    SemanticDependencyKind,
    SemanticProgram,
    SourceSite,
    SyntaxDiagnosticCode,
    UnresolvedAccess,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)

_IMPORT_SOURCE_KINDS = frozenset(
    {
        ResolvedSymbolKind.MODULE,
        ResolvedSymbolKind.CLASS,
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.METHOD,
    }
)
_CALL_SOURCE_KINDS = frozenset(
    {
        ResolvedSymbolKind.MODULE,
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.METHOD,
    }
)
_DECORATOR_TARGET_KINDS = frozenset(
    {
        ResolvedSymbolKind.CLASS,
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.METHOD,
    }
)
_CLASS_ONLY_KINDS = frozenset({ResolvedSymbolKind.CLASS})


@dataclass(frozen=True)
class _SimpleNameExpression:
    """Supported single-name surface for dependency/frontier derivation."""

    name: str


@dataclass(frozen=True)
class _DirectAttributeExpression:
    """Supported ``name.attribute`` surface for dependency/frontier derivation."""

    base_name: str
    attribute_name: str


_SupportedExpression = _SimpleNameExpression | _DirectAttributeExpression


@dataclass(frozen=True)
class _ProgramIndex:
    """Lookup structures derived from accepted syntax and resolver outputs."""

    blocked_file_paths: frozenset[str]
    definitions_by_id: dict[str, RawDefinitionFact]
    resolved_symbols: dict[str, ResolvedSymbol]
    resolved_references_by_id: dict[str, ResolvedReference]
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport]
    decorators_by_reference_id: dict[str, DecoratorFact]
    base_expressions_by_reference_id: dict[str, BaseExpressionFact]


def derive_dependency_frontier(program: SemanticProgram) -> SemanticProgram:
    """Derive proven dependencies plus explicit frontier and unsupported records."""
    index = _build_program_index(program)
    proven_dependencies = _derive_proven_dependencies(program, index)
    unresolved_frontier, unsupported_constructs = _derive_frontier_records(
        program,
        index,
    )

    return SemanticProgram(
        repo_root=program.repo_root,
        syntax=program.syntax,
        supported_subset=program.supported_subset,
        resolved_symbols=program.resolved_symbols,
        bindings=program.bindings,
        resolved_imports=program.resolved_imports,
        dataclass_models=program.dataclass_models,
        dataclass_fields=program.dataclass_fields,
        resolved_references=program.resolved_references,
        proven_dependencies=proven_dependencies,
        unresolved_frontier=unresolved_frontier,
        unsupported_constructs=unsupported_constructs,
        diagnostics=program.diagnostics,
    )


def _build_program_index(program: SemanticProgram) -> _ProgramIndex:
    """Build reusable indices for dependency and frontier derivation."""
    blocked_file_ids = frozenset(
        diagnostic.file_id
        for diagnostic in program.syntax.diagnostics
        if diagnostic.code is SyntaxDiagnosticCode.PARSE_ERROR
    )
    blocked_file_paths = frozenset(
        source_file.path
        for file_id, source_file in program.syntax.source_files.items()
        if file_id in blocked_file_ids
    )
    definitions_by_id = {
        definition.definition_id: definition
        for definition in program.syntax.definitions
        if definition.file_id not in blocked_file_ids
    }

    return _ProgramIndex(
        blocked_file_paths=blocked_file_paths,
        definitions_by_id=definitions_by_id,
        resolved_symbols=program.resolved_symbols,
        resolved_references_by_id={
            resolved_reference.reference_id: resolved_reference
            for resolved_reference in program.resolved_references
        },
        resolved_imports_by_binding_symbol_id={
            resolved_import.binding_symbol_id: resolved_import
            for resolved_import in program.resolved_imports
        },
        decorators_by_reference_id={
            f"reference:{decorator.decorator_id}": decorator
            for decorator in program.syntax.decorators
            if decorator.site.file_path not in blocked_file_paths
        },
        base_expressions_by_reference_id={
            f"reference:{base_expression.base_expression_id}": base_expression
            for base_expression in program.syntax.base_expressions
            if base_expression.site.file_path not in blocked_file_paths
        },
    )


def _derive_proven_dependencies(
    program: SemanticProgram,
    index: _ProgramIndex,
) -> list[SemanticDependency]:
    """Return conservative dependency records backed by resolver proof."""
    dependencies: list[SemanticDependency] = []
    seen_dependency_ids: set[str] = set()

    for resolved_import in program.resolved_imports:
        target_symbol_id = resolved_import.target_symbol_id
        if (
            resolved_import.site.file_path in index.blocked_file_paths
            or target_symbol_id is None
        ):
            continue
        if not _symbol_kind_matches(
            resolved_import.scope_id,
            index,
            allowed_kinds=_IMPORT_SOURCE_KINDS,
        ):
            continue
        dependency = SemanticDependency(
            dependency_id=f"dependency:import:{resolved_import.import_id}",
            source_symbol_id=resolved_import.scope_id,
            target_symbol_id=target_symbol_id,
            kind=SemanticDependencyKind.IMPORT,
            proof_kind=DependencyProofKind.IMPORT_RESOLUTION,
            evidence_site_id=resolved_import.site.site_id,
        )
        _append_unique_dependency(
            dependency=dependency,
            seen_dependency_ids=seen_dependency_ids,
            dependencies=dependencies,
        )

    for resolved_reference in program.resolved_references:
        if resolved_reference.site.file_path in index.blocked_file_paths:
            continue
        reference_dependency = _dependency_for_resolved_reference(
            resolved_reference=resolved_reference,
            index=index,
        )
        if reference_dependency is None:
            continue
        _append_unique_dependency(
            dependency=reference_dependency,
            seen_dependency_ids=seen_dependency_ids,
            dependencies=dependencies,
        )

    return dependencies


def _dependency_for_resolved_reference(
    *,
    resolved_reference: ResolvedReference,
    index: _ProgramIndex,
) -> SemanticDependency | None:
    """Return the dependency proven by one resolver-owned reference, if any."""
    target_symbol_id = resolved_reference.resolved_symbol_id
    if not _is_repository_backed_reference_target(target_symbol_id, index):
        return None

    if resolved_reference.context is ReferenceContext.CALL:
        if not _symbol_kind_matches(
            resolved_reference.enclosing_scope_id,
            index,
            allowed_kinds=_CALL_SOURCE_KINDS,
        ):
            return None
        return SemanticDependency(
            dependency_id=f"dependency:call:{resolved_reference.reference_id}",
            source_symbol_id=resolved_reference.enclosing_scope_id,
            target_symbol_id=target_symbol_id,
            kind=SemanticDependencyKind.CALL,
            proof_kind=DependencyProofKind.CALL_RESOLUTION,
            evidence_site_id=resolved_reference.site.site_id,
            evidence_reference_id=resolved_reference.reference_id,
        )

    if resolved_reference.context is ReferenceContext.BASE_CLASS:
        base_expression = index.base_expressions_by_reference_id.get(
            resolved_reference.reference_id
        )
        if base_expression is None:
            return None
        if not _symbol_kind_matches(
            base_expression.owner_definition_id,
            index,
            allowed_kinds=_CLASS_ONLY_KINDS,
        ):
            return None
        if not _symbol_kind_matches(
            target_symbol_id,
            index,
            allowed_kinds=_CLASS_ONLY_KINDS,
        ):
            return None
        return SemanticDependency(
            dependency_id=f"dependency:base:{resolved_reference.reference_id}",
            source_symbol_id=base_expression.owner_definition_id,
            target_symbol_id=target_symbol_id,
            kind=SemanticDependencyKind.INHERITANCE,
            proof_kind=DependencyProofKind.BASE_CLASS_RESOLUTION,
            evidence_site_id=resolved_reference.site.site_id,
            evidence_reference_id=resolved_reference.reference_id,
        )

    if resolved_reference.context is ReferenceContext.DECORATOR:
        decorator = index.decorators_by_reference_id.get(
            resolved_reference.reference_id
        )
        if decorator is None:
            return None
        if not _symbol_kind_matches(
            decorator.owner_definition_id,
            index,
            allowed_kinds=_DECORATOR_TARGET_KINDS,
        ):
            return None
        if not _symbol_kind_matches(
            target_symbol_id,
            index,
            allowed_kinds=_DECORATOR_TARGET_KINDS,
        ):
            return None
        return SemanticDependency(
            dependency_id=f"dependency:decorator:{resolved_reference.reference_id}",
            source_symbol_id=decorator.owner_definition_id,
            target_symbol_id=target_symbol_id,
            kind=SemanticDependencyKind.DECORATOR,
            proof_kind=DependencyProofKind.DECORATOR_RESOLUTION,
            evidence_site_id=resolved_reference.site.site_id,
            evidence_reference_id=resolved_reference.reference_id,
        )

    return None


def _append_unique_dependency(
    *,
    dependency: SemanticDependency,
    seen_dependency_ids: set[str],
    dependencies: list[SemanticDependency],
) -> None:
    """Append ``dependency`` only once for its concrete proof event."""
    if dependency.dependency_id in seen_dependency_ids:
        return
    seen_dependency_ids.add(dependency.dependency_id)
    dependencies.append(dependency)


def _derive_frontier_records(
    program: SemanticProgram,
    index: _ProgramIndex,
) -> tuple[list[UnresolvedAccess], list[UnsupportedConstruct]]:
    """Return unresolved frontier and unsupported construct records."""
    unresolved_frontier: list[UnresolvedAccess] = []
    unsupported_constructs: list[UnsupportedConstruct] = []

    for import_fact in program.syntax.imports:
        if (
            import_fact.kind is not ImportKind.STAR_IMPORT
            or import_fact.site.file_path in index.blocked_file_paths
        ):
            continue
        unsupported_constructs.append(
            UnsupportedConstruct(
                construct_id=f"unsupported:{import_fact.import_id}",
                site=import_fact.site,
                construct_text=(
                    import_fact.site.snippet.strip()
                    if import_fact.site.snippet is not None
                    else _format_import_fact(import_fact)
                ),
                reason_code=UnresolvedReasonCode.STAR_IMPORT,
                enclosing_scope_id=import_fact.scope_id,
            )
        )

    for decorator in program.syntax.decorators:
        if decorator.site.file_path in index.blocked_file_paths:
            continue
        if f"reference:{decorator.decorator_id}" in index.resolved_references_by_id:
            continue
        owner_definition = index.definitions_by_id.get(decorator.owner_definition_id)
        if owner_definition is None or owner_definition.parent_definition_id is None:
            continue
        _append_reference_frontier_record(
            fact_id=decorator.decorator_id,
            expression_text=decorator.expression_text,
            site=decorator.site,
            context=ReferenceContext.DECORATOR,
            enclosing_scope_id=owner_definition.parent_definition_id,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=_decorator_unsupported_reason(decorator),
        )

    for base_expression in program.syntax.base_expressions:
        if base_expression.site.file_path in index.blocked_file_paths:
            continue
        if (
            f"reference:{base_expression.base_expression_id}"
            in index.resolved_references_by_id
        ):
            continue
        owner_definition = index.definitions_by_id.get(
            base_expression.owner_definition_id
        )
        if owner_definition is None or owner_definition.parent_definition_id is None:
            continue
        _append_reference_frontier_record(
            fact_id=base_expression.base_expression_id,
            expression_text=base_expression.expression_text,
            site=base_expression.site,
            context=ReferenceContext.BASE_CLASS,
            enclosing_scope_id=owner_definition.parent_definition_id,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=UnresolvedReasonCode.UNSUPPORTED_BASE_EXPRESSION,
        )

    for call_site in program.syntax.call_sites:
        if call_site.site.file_path in index.blocked_file_paths:
            continue
        if f"reference:{call_site.call_site_id}" in index.resolved_references_by_id:
            continue
        _append_reference_frontier_record(
            fact_id=call_site.call_site_id,
            expression_text=call_site.callee_text,
            site=call_site.site,
            context=ReferenceContext.CALL,
            enclosing_scope_id=call_site.enclosing_scope_id,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        )

    return unresolved_frontier, unsupported_constructs


def _append_reference_frontier_record(
    *,
    fact_id: str,
    expression_text: str,
    site: SourceSite,
    context: ReferenceContext,
    enclosing_scope_id: str,
    unresolved_frontier: list[UnresolvedAccess],
    unsupported_constructs: list[UnsupportedConstruct],
    unsupported_reason_code: UnresolvedReasonCode,
) -> None:
    """Append the honest frontier or unsupported record for one reference surface."""
    expression = _parse_supported_expression(expression_text)
    if expression is None:
        unsupported_constructs.append(
            UnsupportedConstruct(
                construct_id=f"unsupported:{fact_id}",
                site=site,
                construct_text=expression_text,
                reason_code=unsupported_reason_code,
                enclosing_scope_id=enclosing_scope_id,
            )
        )
        return

    reason_code = (
        UnresolvedReasonCode.UNRESOLVED_NAME
        if isinstance(expression, _SimpleNameExpression)
        else UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE
    )
    unresolved_frontier.append(
        UnresolvedAccess(
            access_id=f"frontier:{fact_id}",
            site=site,
            access_text=expression_text,
            context=context,
            enclosing_scope_id=enclosing_scope_id,
            reason_code=reason_code,
        )
    )


def _decorator_unsupported_reason(
    decorator: DecoratorFact,
) -> UnresolvedReasonCode:
    """Return the most truthful unsupported reason for ``decorator``."""
    if decorator.support is DecoratorSupport.OPAQUE:
        return UnresolvedReasonCode.OPAQUE_DECORATOR
    return UnresolvedReasonCode.UNSUPPORTED_DECORATOR


def _parse_supported_expression(expression_text: str) -> _SupportedExpression | None:
    """Parse one supported simple-name or direct-attribute reference surface."""
    try:
        expression = ast.parse(expression_text, mode="eval").body
    except SyntaxError:
        return None

    if isinstance(expression, ast.Name) and _is_simple_identifier(expression.id):
        return _SimpleNameExpression(name=expression.id)
    if (
        isinstance(expression, ast.Attribute)
        and isinstance(expression.value, ast.Name)
        and _is_simple_identifier(expression.value.id)
        and _is_simple_identifier(expression.attr)
    ):
        return _DirectAttributeExpression(
            base_name=expression.value.id,
            attribute_name=expression.attr,
        )
    return None


def _is_simple_identifier(name: str) -> bool:
    """Return whether ``name`` is a plain identifier surface."""
    return name.isidentifier() and not keyword.iskeyword(name)


def _is_repository_backed_reference_target(
    symbol_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``symbol_id`` names a repository-backed resolved target."""
    external_import = index.resolved_imports_by_binding_symbol_id.get(symbol_id)
    if (
        external_import is not None
        and external_import.target_kind is ImportTargetKind.EXTERNAL
    ):
        return False
    return symbol_id in index.resolved_symbols


def _symbol_kind_matches(
    symbol_id: str,
    index: _ProgramIndex,
    *,
    allowed_kinds: frozenset[ResolvedSymbolKind],
) -> bool:
    """Return whether ``symbol_id`` resolves to one of ``allowed_kinds``."""
    symbol = index.resolved_symbols.get(symbol_id)
    return symbol is not None and symbol.kind in allowed_kinds


def _format_import_fact(import_fact: ImportFact) -> str:
    """Return a stable textual fallback for unsupported star-import facts."""
    if import_fact.kind is ImportKind.IMPORT:
        if import_fact.alias is None:
            return f"import {import_fact.module_name}"
        return f"import {import_fact.module_name} as {import_fact.alias}"
    if import_fact.imported_name == "*":
        return f"from {import_fact.module_name} import *"
    imported_name = import_fact.imported_name or ""
    if import_fact.alias is None:
        return f"from {import_fact.module_name} import {imported_name}"
    return (
        f"from {import_fact.module_name} import {imported_name} as {import_fact.alias}"
    )


__all__ = ["derive_dependency_frontier"]
