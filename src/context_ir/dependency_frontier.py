"""Semantic dependency and frontier derivation for the semantic-first baseline."""

from __future__ import annotations

import ast
import keyword
from dataclasses import dataclass

from context_ir.semantic_types import (
    AssignmentFact,
    AttributeSiteFact,
    BaseExpressionFact,
    BindingFact,
    BindingKind,
    CallSiteFact,
    DecoratorFact,
    DecoratorSupport,
    DefinitionKind,
    DependencyProofKind,
    ImportFact,
    ImportKind,
    ImportTargetKind,
    MetaclassKeywordFact,
    ParameterFact,
    ParameterKind,
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
    SourceSpan,
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
_ATTRIBUTE_SOURCE_KINDS = _CALL_SOURCE_KINDS
_ATTRIBUTE_TARGET_KINDS = frozenset({ResolvedSymbolKind.ATTRIBUTE})
_DECORATOR_TARGET_KINDS = frozenset(
    {
        ResolvedSymbolKind.CLASS,
        ResolvedSymbolKind.FUNCTION,
        ResolvedSymbolKind.ASYNC_FUNCTION,
        ResolvedSymbolKind.METHOD,
    }
)
_CLASS_ONLY_KINDS = frozenset({ResolvedSymbolKind.CLASS})
_FUNCTION_LIKE_KINDS = frozenset(
    {
        DefinitionKind.FUNCTION,
        DefinitionKind.ASYNC_FUNCTION,
        DefinitionKind.METHOD,
    }
)
_MODULE_ATTRIBUTE_HOOK_FUNCTION_NAME = "__getattr__"
_ATTRIBUTE_HOOK_METHOD_NAMES = frozenset({"__getattr__", "__getattribute__"})
_DYNAMIC_CALL_REASON_CODES: dict[str, UnresolvedReasonCode] = {
    "__import__": UnresolvedReasonCode.DYNAMIC_IMPORT,
    "setattr": UnresolvedReasonCode.RUNTIME_MUTATION,
    "delattr": UnresolvedReasonCode.RUNTIME_MUTATION,
    "globals": UnresolvedReasonCode.RUNTIME_MUTATION,
    "locals": UnresolvedReasonCode.RUNTIME_MUTATION,
    "getattr": UnresolvedReasonCode.REFLECTIVE_BUILTIN,
    "hasattr": UnresolvedReasonCode.REFLECTIVE_BUILTIN,
    "vars": UnresolvedReasonCode.REFLECTIVE_BUILTIN,
    "dir": UnresolvedReasonCode.REFLECTIVE_BUILTIN,
    "exec": UnresolvedReasonCode.EXEC_OR_EVAL,
    "eval": UnresolvedReasonCode.EXEC_OR_EVAL,
}


@dataclass(frozen=True)
class _SimpleNameExpression:
    """Supported single-name surface for dependency/frontier derivation."""

    name: str


@dataclass(frozen=True)
class _AttributeChainExpression:
    """Supported dotted surface with up to two attribute hops."""

    root_name: str
    attribute_names: tuple[str, ...]


_SupportedExpression = _SimpleNameExpression | _AttributeChainExpression


@dataclass(frozen=True)
class _ProgramIndex:
    """Lookup structures derived from accepted syntax and resolver outputs."""

    blocked_file_paths: frozenset[str]
    definitions_by_id: dict[str, RawDefinitionFact]
    unique_definitions_by_qualified_name: dict[str, RawDefinitionFact]
    module_qualified_names: frozenset[str]
    resolved_symbols: dict[str, ResolvedSymbol]
    resolved_references_by_id: dict[str, ResolvedReference]
    resolved_imports_by_binding_symbol_id: dict[str, ResolvedImport]
    import_facts_by_binding_symbol_id: dict[str, ImportFact]
    assignments_by_symbol_id: dict[str, AssignmentFact]
    bindings_by_scope: dict[str, list[BindingFact]]
    parameters_by_owner_definition_id: dict[str, tuple[ParameterFact, ...]]
    scope_parent_ids: dict[str, str | None]
    scope_kinds: dict[str, DefinitionKind]
    module_ids_with_getattr_function: frozenset[str]
    class_ids_with_attribute_hook_method: frozenset[str]
    class_ids_with_direct_base_attribute_hook_method: frozenset[str]
    direct_proven_base_class_ids_by_class_id: dict[str, frozenset[str]]
    decorated_definition_ids: frozenset[str]
    decorators_by_reference_id: dict[str, DecoratorFact]
    base_expressions_by_reference_id: dict[str, BaseExpressionFact]
    covered_attribute_surface_signatures: frozenset[tuple[str, int, int, str]]


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
    definitions_by_qualified_name: dict[str, list[RawDefinitionFact]] = {}
    for definition in definitions_by_id.values():
        definitions_by_qualified_name.setdefault(definition.qualified_name, []).append(
            definition
        )
    bindings_by_scope: dict[str, list[BindingFact]] = {}
    for binding in program.bindings:
        if binding.site.file_path in blocked_file_paths:
            continue
        bindings_by_scope.setdefault(binding.scope_id, []).append(binding)
    parameters_by_owner_definition_id: dict[str, list[ParameterFact]] = {}
    for parameter in program.syntax.parameters:
        if (
            parameter.site.file_path in blocked_file_paths
            or parameter.owner_definition_id not in definitions_by_id
        ):
            continue
        parameters_by_owner_definition_id.setdefault(
            parameter.owner_definition_id,
            [],
        ).append(parameter)
    class_ids_with_attribute_hook_method = frozenset(
        definition.parent_definition_id
        for definition in definitions_by_id.values()
        if definition.kind is DefinitionKind.METHOD
        and definition.parent_definition_id is not None
        and definition.name in _ATTRIBUTE_HOOK_METHOD_NAMES
    )
    module_ids_with_getattr_function = frozenset(
        definition.parent_definition_id
        for definition in definitions_by_id.values()
        if definition.kind in _FUNCTION_LIKE_KINDS
        and definition.parent_definition_id is not None
        and definition.name == _MODULE_ATTRIBUTE_HOOK_FUNCTION_NAME
        and (
            parent_definition := definitions_by_id.get(definition.parent_definition_id)
        )
        is not None
        and parent_definition.kind is DefinitionKind.MODULE
    )
    resolved_references_by_id = {
        resolved_reference.reference_id: resolved_reference
        for resolved_reference in program.resolved_references
    }
    base_expressions_by_reference_id = {
        f"reference:{base_expression.base_expression_id}": base_expression
        for base_expression in program.syntax.base_expressions
        if base_expression.site.file_path not in blocked_file_paths
    }
    direct_proven_base_class_ids_by_class_id: dict[str, set[str]] = {}
    class_ids_with_direct_base_attribute_hook_method: set[str] = set()
    for reference_id, base_expression in base_expressions_by_reference_id.items():
        resolved_reference = resolved_references_by_id.get(reference_id)
        owner_definition = definitions_by_id.get(base_expression.owner_definition_id)
        if (
            resolved_reference is None
            or owner_definition is None
            or owner_definition.kind is not DefinitionKind.CLASS
        ):
            continue
        target_definition = definitions_by_id.get(resolved_reference.resolved_symbol_id)
        if (
            target_definition is None
            or target_definition.kind is not DefinitionKind.CLASS
        ):
            continue
        direct_proven_base_class_ids_by_class_id.setdefault(
            owner_definition.definition_id,
            set(),
        ).add(target_definition.definition_id)
        if target_definition.definition_id in class_ids_with_attribute_hook_method:
            class_ids_with_direct_base_attribute_hook_method.add(
                owner_definition.definition_id
            )
    frozen_direct_proven_base_class_ids_by_class_id = {
        class_definition_id: frozenset(base_class_definition_ids)
        for class_definition_id, base_class_definition_ids in (
            direct_proven_base_class_ids_by_class_id.items()
        )
    }

    return _ProgramIndex(
        blocked_file_paths=blocked_file_paths,
        definitions_by_id=definitions_by_id,
        unique_definitions_by_qualified_name={
            qualified_name: definitions[0]
            for qualified_name, definitions in definitions_by_qualified_name.items()
            if len(definitions) == 1
        },
        module_qualified_names=frozenset(
            definition.qualified_name
            for definition in definitions_by_id.values()
            if definition.kind is DefinitionKind.MODULE
        ),
        resolved_symbols=program.resolved_symbols,
        resolved_references_by_id=resolved_references_by_id,
        resolved_imports_by_binding_symbol_id={
            resolved_import.binding_symbol_id: resolved_import
            for resolved_import in program.resolved_imports
        },
        import_facts_by_binding_symbol_id={
            import_fact.import_id: import_fact
            for import_fact in program.syntax.imports
            if import_fact.site.file_path not in blocked_file_paths
        },
        assignments_by_symbol_id={
            assignment.assignment_id: assignment
            for assignment in program.syntax.assignments
            if assignment.site.file_path not in blocked_file_paths
        },
        bindings_by_scope=bindings_by_scope,
        parameters_by_owner_definition_id={
            owner_definition_id: tuple(owner_parameters)
            for owner_definition_id, owner_parameters in (
                parameters_by_owner_definition_id.items()
            )
        },
        scope_parent_ids={
            definition.definition_id: definition.parent_definition_id
            for definition in definitions_by_id.values()
        },
        scope_kinds={
            definition.definition_id: definition.kind
            for definition in definitions_by_id.values()
        },
        module_ids_with_getattr_function=module_ids_with_getattr_function,
        class_ids_with_attribute_hook_method=class_ids_with_attribute_hook_method,
        class_ids_with_direct_base_attribute_hook_method=(
            frozenset(class_ids_with_direct_base_attribute_hook_method)
        ),
        direct_proven_base_class_ids_by_class_id=(
            frozen_direct_proven_base_class_ids_by_class_id
        ),
        decorated_definition_ids=frozenset(
            decorator.owner_definition_id
            for decorator in program.syntax.decorators
            if decorator.site.file_path not in blocked_file_paths
            and decorator.owner_definition_id in definitions_by_id
        ),
        decorators_by_reference_id={
            f"reference:{decorator.decorator_id}": decorator
            for decorator in program.syntax.decorators
            if decorator.site.file_path not in blocked_file_paths
        },
        base_expressions_by_reference_id=base_expressions_by_reference_id,
        covered_attribute_surface_signatures=frozenset(
            _surface_signature(
                site=decorator.site,
                expression_text=decorator.expression_text,
            )
            for decorator in program.syntax.decorators
            if decorator.site.file_path not in blocked_file_paths
        )
        | frozenset(
            _surface_signature(
                site=base_expression.site,
                expression_text=base_expression.expression_text,
            )
            for base_expression in program.syntax.base_expressions
            if base_expression.site.file_path not in blocked_file_paths
        )
        | frozenset(
            _surface_signature(
                site=call_site.site,
                expression_text=call_site.callee_text,
            )
            for call_site in program.syntax.call_sites
            if call_site.site.file_path not in blocked_file_paths
        )
        | frozenset(
            _surface_signature(
                site=resolved_reference.site,
                expression_text=expression_text,
            )
            for resolved_reference in program.resolved_references
            for expression_text in _attribute_surface_expressions(
                resolved_reference.name
            )
        ),
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

    if resolved_reference.context is ReferenceContext.ATTRIBUTE_ACCESS:
        if not _symbol_kind_matches(
            resolved_reference.enclosing_scope_id,
            index,
            allowed_kinds=_ATTRIBUTE_SOURCE_KINDS,
        ):
            return None
        if not _symbol_kind_matches(
            target_symbol_id,
            index,
            allowed_kinds=_ATTRIBUTE_TARGET_KINDS,
        ):
            return None
        return SemanticDependency(
            dependency_id=f"dependency:attribute:{resolved_reference.reference_id}",
            source_symbol_id=resolved_reference.enclosing_scope_id,
            target_symbol_id=target_symbol_id,
            kind=SemanticDependencyKind.ATTRIBUTE,
            proof_kind=DependencyProofKind.ATTRIBUTE_RESOLUTION,
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
            index=index,
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
            index=index,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=UnresolvedReasonCode.UNSUPPORTED_BASE_EXPRESSION,
        )

    for metaclass_keyword in program.syntax.metaclass_keywords:
        if metaclass_keyword.site.file_path in index.blocked_file_paths:
            continue
        owner_definition = index.definitions_by_id.get(
            metaclass_keyword.owner_definition_id
        )
        if owner_definition is None or owner_definition.parent_definition_id is None:
            continue
        unsupported_constructs.append(
            UnsupportedConstruct(
                construct_id=f"unsupported:{metaclass_keyword.metaclass_keyword_id}",
                site=metaclass_keyword.site,
                construct_text=_metaclass_keyword_construct_text(metaclass_keyword),
                reason_code=UnresolvedReasonCode.METACLASS_BEHAVIOR,
                enclosing_scope_id=owner_definition.parent_definition_id,
            )
        )

    for call_site in program.syntax.call_sites:
        if call_site.site.file_path in index.blocked_file_paths:
            continue
        if f"reference:{call_site.call_site_id}" in index.resolved_references_by_id:
            continue
        dynamic_construct = _unsupported_dynamic_construct_for_call_site(
            call_site=call_site,
            index=index,
        )
        if dynamic_construct is not None:
            unsupported_constructs.append(dynamic_construct)
            continue
        _append_reference_frontier_record(
            fact_id=call_site.call_site_id,
            expression_text=call_site.callee_text,
            site=call_site.site,
            context=ReferenceContext.CALL,
            enclosing_scope_id=call_site.enclosing_scope_id,
            index=index,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=UnresolvedReasonCode.UNSUPPORTED_CALL_TARGET,
        )

    for attribute_site in program.syntax.attribute_sites:
        if attribute_site.site.file_path in index.blocked_file_paths:
            continue
        expression_text = _format_attribute_site(attribute_site)
        if (
            _surface_signature(
                site=attribute_site.site,
                expression_text=expression_text,
            )
            in index.covered_attribute_surface_signatures
        ):
            continue
        _append_reference_frontier_record(
            fact_id=_attribute_frontier_fact_id(attribute_site),
            expression_text=expression_text,
            site=attribute_site.site,
            context=attribute_site.context,
            enclosing_scope_id=attribute_site.enclosing_scope_id,
            index=index,
            unresolved_frontier=unresolved_frontier,
            unsupported_constructs=unsupported_constructs,
            unsupported_reason_code=UnresolvedReasonCode.UNSUPPORTED_ATTRIBUTE_ACCESS,
        )

    return unresolved_frontier, unsupported_constructs


def _unsupported_dynamic_construct_for_call_site(
    *,
    call_site: CallSiteFact,
    index: _ProgramIndex,
) -> UnsupportedConstruct | None:
    """Return the explicit unsupported record for named dynamic call boundaries."""
    reason_code = _dynamic_boundary_reason_for_call_site(
        call_site=call_site,
        index=index,
    )
    if reason_code is None:
        return None
    return UnsupportedConstruct(
        construct_id=f"unsupported:{call_site.call_site_id}",
        site=call_site.site,
        construct_text=_call_site_construct_text(call_site),
        reason_code=reason_code,
        enclosing_scope_id=call_site.enclosing_scope_id,
    )


def _dynamic_boundary_reason_for_call_site(
    *,
    call_site: CallSiteFact,
    index: _ProgramIndex,
) -> UnresolvedReasonCode | None:
    """Return the named dynamic-boundary reason for one unresolved call site."""
    expression = _parse_supported_expression(call_site.callee_text)
    if isinstance(expression, _SimpleNameExpression):
        binding = _lookup_visible_binding(
            name=expression.name,
            scope_id=call_site.enclosing_scope_id,
            site=call_site.site,
            index=index,
        )
        if binding is not None:
            if _binding_is_importlib_import_module_import(binding=binding, index=index):
                return UnresolvedReasonCode.DYNAMIC_IMPORT
            return None
        return _DYNAMIC_CALL_REASON_CODES.get(expression.name)
    if not (
        isinstance(expression, _AttributeChainExpression)
        and expression.attribute_names == ("import_module",)
    ):
        return None
    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=call_site.enclosing_scope_id,
        site=call_site.site,
        index=index,
    )
    if not _binding_is_importlib_root_import(binding=binding, index=index):
        return None
    return UnresolvedReasonCode.DYNAMIC_IMPORT


def _call_site_construct_text(call_site: CallSiteFact) -> str:
    """Return the most specific available source text for one call site."""
    if call_site.site.snippet is not None:
        return call_site.site.snippet.strip()
    return call_site.callee_text


def _metaclass_keyword_construct_text(
    metaclass_keyword: MetaclassKeywordFact,
) -> str:
    """Return the most specific available source text for one metaclass keyword."""
    if metaclass_keyword.site.snippet is not None:
        return metaclass_keyword.site.snippet.strip()
    return metaclass_keyword.keyword_text.strip()


def _append_reference_frontier_record(
    *,
    fact_id: str,
    expression_text: str,
    site: SourceSite,
    context: ReferenceContext,
    enclosing_scope_id: str,
    index: _ProgramIndex,
    unresolved_frontier: list[UnresolvedAccess],
    unsupported_constructs: list[UnsupportedConstruct],
    unsupported_reason_code: UnresolvedReasonCode,
) -> None:
    """Append the honest frontier or unsupported record for one reference surface."""
    expression = _parse_supported_expression(expression_text)
    if expression is None or not _is_supported_frontier_expression(
        expression=expression,
        site=site,
        enclosing_scope_id=enclosing_scope_id,
        index=index,
    ):
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

    if _is_hook_affected_same_class_self_expression(
        expression=expression,
        site=site,
        enclosing_scope_id=enclosing_scope_id,
        index=index,
    ):
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

    if _is_hook_affected_import_rooted_module_expression(
        expression=expression,
        context=context,
        site=site,
        enclosing_scope_id=enclosing_scope_id,
        index=index,
    ):
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

    reason_code = _unresolved_reason_code_for_expression(
        expression=expression,
        site=site,
        enclosing_scope_id=enclosing_scope_id,
        index=index,
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


def _format_attribute_site(attribute_site: AttributeSiteFact) -> str:
    """Return the stable source text for one attribute site."""
    return f"{attribute_site.base_text}.{attribute_site.attribute_name}"


def _attribute_frontier_fact_id(attribute_site: AttributeSiteFact) -> str:
    """Return a stable frontier/unsupported fact id for one attribute site."""
    span = attribute_site.site.span
    return f"{attribute_site.attribute_site_id}:{span.end_line}:{span.end_column}"


def _unresolved_reason_code_for_expression(
    *,
    expression: _SupportedExpression,
    site: SourceSite,
    enclosing_scope_id: str,
    index: _ProgramIndex,
) -> UnresolvedReasonCode:
    """Return the most truthful unresolved reason for one supported surface."""
    root_name = (
        expression.name
        if isinstance(expression, _SimpleNameExpression)
        else expression.root_name
    )
    binding = _lookup_visible_binding(
        name=root_name,
        scope_id=enclosing_scope_id,
        site=site,
        index=index,
    )
    if binding is not None and _binding_is_shallow_import_alias(
        binding=binding,
        index=index,
    ):
        return UnresolvedReasonCode.ALIAS_CHAIN
    if isinstance(expression, _SimpleNameExpression):
        return UnresolvedReasonCode.UNRESOLVED_NAME
    return UnresolvedReasonCode.UNRESOLVED_ATTRIBUTE


def _is_hook_affected_same_class_self_expression(
    *,
    expression: _SupportedExpression,
    site: SourceSite,
    enclosing_scope_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether one unresolved direct ``self.*`` surface hits a hook boundary."""
    if not isinstance(expression, _AttributeChainExpression):
        return False
    if expression.root_name != "self" or len(expression.attribute_names) != 1:
        return False
    attribute_name = expression.attribute_names[0]
    if attribute_name in _ATTRIBUTE_HOOK_METHOD_NAMES:
        return False

    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=enclosing_scope_id,
        site=site,
        index=index,
    )
    if binding is None or binding.binding_kind is not BindingKind.PARAMETER:
        return False

    method_definition = index.definitions_by_id.get(enclosing_scope_id)
    if method_definition is None or method_definition.kind is not DefinitionKind.METHOD:
        return False
    if method_definition.definition_id in index.decorated_definition_ids:
        return False
    if not _is_canonical_self_parameter(
        parameter_symbol_id=binding.symbol_id,
        method_definition_id=method_definition.definition_id,
        index=index,
    ):
        return False

    class_definition_id = method_definition.parent_definition_id
    return class_definition_id is not None and (
        class_definition_id in index.class_ids_with_attribute_hook_method
        or class_definition_id in index.class_ids_with_direct_base_attribute_hook_method
        or _has_transitively_proven_ancestor_with_attribute_hook(
            class_definition_id=class_definition_id,
            index=index,
        )
    )


def _is_hook_affected_import_rooted_module_expression(
    *,
    expression: _SupportedExpression,
    context: ReferenceContext,
    site: SourceSite,
    enclosing_scope_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether one direct import-rooted module surface hits ``__getattr__``."""
    if context not in {
        ReferenceContext.CALL,
        ReferenceContext.ATTRIBUTE_ACCESS,
        ReferenceContext.STORE,
    }:
        return False
    if not isinstance(expression, _AttributeChainExpression):
        return False
    if len(expression.attribute_names) != 1:
        return False
    if expression.attribute_names[0] == _MODULE_ATTRIBUTE_HOOK_FUNCTION_NAME:
        return False

    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=enclosing_scope_id,
        site=site,
        index=index,
    )
    if binding is None or binding.binding_kind is not BindingKind.IMPORT:
        return False

    resolved_import = index.resolved_imports_by_binding_symbol_id.get(binding.symbol_id)
    if (
        resolved_import is None
        or resolved_import.target_kind is not ImportTargetKind.MODULE
    ):
        return False
    target_symbol_id = resolved_import.target_symbol_id
    return (
        target_symbol_id is not None
        and target_symbol_id in index.module_ids_with_getattr_function
    )


def _has_transitively_proven_ancestor_with_attribute_hook(
    *,
    class_definition_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether any proven ancestor defines an attribute hook method."""
    pending_class_definition_ids = sorted(
        index.direct_proven_base_class_ids_by_class_id.get(
            class_definition_id,
            frozenset(),
        ),
        reverse=True,
    )
    seen_class_definition_ids: set[str] = set()
    while pending_class_definition_ids:
        candidate_class_definition_id = pending_class_definition_ids.pop()
        if candidate_class_definition_id in seen_class_definition_ids:
            continue
        seen_class_definition_ids.add(candidate_class_definition_id)
        if candidate_class_definition_id in index.class_ids_with_attribute_hook_method:
            return True
        pending_class_definition_ids.extend(
            sorted(
                index.direct_proven_base_class_ids_by_class_id.get(
                    candidate_class_definition_id,
                    frozenset(),
                ),
                reverse=True,
            )
        )
    return False


def _is_canonical_self_parameter(
    *,
    parameter_symbol_id: str,
    method_definition_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``parameter_symbol_id`` is the canonical first ``self``."""
    parameters = index.parameters_by_owner_definition_id.get(method_definition_id)
    if not parameters:
        return False
    first_parameter = min(parameters, key=lambda parameter: parameter.ordinal)
    return (
        first_parameter.parameter_id == parameter_symbol_id
        and first_parameter.name == "self"
        and first_parameter.kind
        in {
            ParameterKind.POSITIONAL_ONLY,
            ParameterKind.POSITIONAL_OR_KEYWORD,
        }
    )


def _is_supported_frontier_expression(
    *,
    expression: _SupportedExpression,
    site: SourceSite,
    enclosing_scope_id: str,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``expression`` stays inside the accepted frontier surface."""
    if isinstance(expression, _SimpleNameExpression):
        return True
    if len(expression.attribute_names) == 1:
        return True
    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=enclosing_scope_id,
        site=site,
        index=index,
    )
    if binding is None:
        return False
    if binding.binding_kind is BindingKind.IMPORT:
        return True
    return _binding_is_shallow_import_alias(binding=binding, index=index)


def _surface_signature(
    *,
    site: SourceSite,
    expression_text: str,
) -> tuple[str, int, int, str]:
    """Return a stable signature for one reference-shaped surface."""
    return (
        site.file_path,
        site.span.start_line,
        site.span.start_column,
        expression_text,
    )


def _parse_supported_expression(expression_text: str) -> _SupportedExpression | None:
    """Parse one supported simple-name or narrow dotted reference surface."""
    try:
        expression = ast.parse(expression_text, mode="eval").body
    except SyntaxError:
        return None

    if isinstance(expression, ast.Name) and _is_simple_identifier(expression.id):
        return _SimpleNameExpression(name=expression.id)
    attribute_names: list[str] = []
    current_expression: ast.expr = expression
    while isinstance(current_expression, ast.Attribute):
        if not _is_simple_identifier(current_expression.attr):
            return None
        attribute_names.append(current_expression.attr)
        if len(attribute_names) > 2:
            return None
        current_expression = current_expression.value
    if (
        attribute_names
        and isinstance(current_expression, ast.Name)
        and _is_simple_identifier(current_expression.id)
    ):
        return _AttributeChainExpression(
            root_name=current_expression.id,
            attribute_names=tuple(reversed(attribute_names)),
        )
    return None


def _attribute_surface_expressions(expression_text: str) -> tuple[str, ...]:
    """Return attribute-shaped prefixes covered by one resolved reference."""
    expression = _parse_supported_expression(expression_text)
    if not isinstance(expression, _AttributeChainExpression):
        return ()
    return tuple(
        ".".join((expression.root_name, *expression.attribute_names[:attribute_count]))
        for attribute_count in range(1, len(expression.attribute_names) + 1)
    )


def _is_simple_identifier(name: str) -> bool:
    """Return whether ``name`` is a plain identifier surface."""
    return name.isidentifier() and not keyword.iskeyword(name)


def _lookup_visible_binding(
    *,
    name: str,
    scope_id: str,
    site: SourceSite,
    index: _ProgramIndex,
) -> BindingFact | None:
    """Return the nearest visible binding for ``name`` in lexical scope order."""
    current_scope_id: str | None = scope_id
    while current_scope_id is not None:
        for binding in reversed(index.bindings_by_scope.get(current_scope_id, [])):
            if binding.name != name:
                continue
            if not _binding_is_visible(binding=binding, site=site):
                continue
            return binding
        current_scope_id = _next_scope_id_for_lookup(current_scope_id, index)
    return None


def _binding_is_visible(
    *,
    binding: BindingFact,
    site: SourceSite,
) -> bool:
    """Return whether ``binding`` is available at ``site`` conservatively."""
    if binding.site.file_path != site.file_path:
        return False
    if binding.binding_kind is BindingKind.PARAMETER:
        return True
    if binding.binding_kind is BindingKind.DEFINITION:
        return _span_starts_before(binding.site.span, site.span)
    return _span_ends_before_or_at(binding.site.span, site.span)


def _next_scope_id_for_lookup(
    scope_id: str,
    index: _ProgramIndex,
) -> str | None:
    """Return the next lexical scope to search, skipping class scopes for closures."""
    parent_scope_id = index.scope_parent_ids.get(scope_id)
    if parent_scope_id is None:
        return None
    current_kind = index.scope_kinds.get(scope_id)
    parent_kind = index.scope_kinds.get(parent_scope_id)
    if current_kind in _FUNCTION_LIKE_KINDS and parent_kind is DefinitionKind.CLASS:
        return index.scope_parent_ids.get(parent_scope_id)
    return parent_scope_id


def _binding_is_shallow_import_alias(
    *,
    binding: BindingFact,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``binding`` is a shallow local alias rooted in an import."""
    if binding.binding_kind is not BindingKind.ASSIGNMENT:
        return False
    assignment = index.assignments_by_symbol_id.get(binding.symbol_id)
    if assignment is None or assignment.value_text is None:
        return False
    return _is_import_backed_reference(
        expression_text=assignment.value_text,
        scope_id=assignment.scope_id,
        site=assignment.site,
        index=index,
    )


def _binding_is_importlib_root_import(
    *,
    binding: BindingFact | None,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``binding`` names the imported ``importlib`` root module."""
    if binding is None or binding.binding_kind is not BindingKind.IMPORT:
        return False
    import_fact = index.import_facts_by_binding_symbol_id.get(binding.symbol_id)
    if import_fact is None or import_fact.kind is not ImportKind.IMPORT:
        return False
    return import_fact.module_name == "importlib"


def _binding_is_importlib_import_module_import(
    *,
    binding: BindingFact,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``binding`` is ``from importlib import import_module``."""
    if binding.binding_kind is not BindingKind.IMPORT:
        return False
    import_fact = index.import_facts_by_binding_symbol_id.get(binding.symbol_id)
    if import_fact is None or import_fact.kind is not ImportKind.FROM_IMPORT:
        return False
    return (
        import_fact.module_name == "importlib"
        and import_fact.imported_name == "import_module"
    )


def _is_import_backed_reference(
    *,
    expression_text: str,
    scope_id: str,
    site: SourceSite,
    index: _ProgramIndex,
) -> bool:
    """Return whether ``expression_text`` is a shallow repo import-backed reference."""
    expression = _parse_supported_expression(expression_text)
    if expression is None:
        return False

    if isinstance(expression, _SimpleNameExpression):
        binding = _lookup_visible_binding(
            name=expression.name,
            scope_id=scope_id,
            site=site,
            index=index,
        )
        if binding is None or binding.binding_kind is not BindingKind.IMPORT:
            return False
        resolved_import = index.resolved_imports_by_binding_symbol_id.get(
            binding.symbol_id
        )
        return bool(
            resolved_import is not None
            and resolved_import.target_kind
            in {ImportTargetKind.MODULE, ImportTargetKind.DEFINITION}
        )

    binding = _lookup_visible_binding(
        name=expression.root_name,
        scope_id=scope_id,
        site=site,
        index=index,
    )
    if binding is None or binding.binding_kind is not BindingKind.IMPORT:
        return False
    return _import_rooted_chain_is_provable(
        binding_symbol_id=binding.symbol_id,
        attribute_names=expression.attribute_names,
        index=index,
    )


def _import_rooted_chain_is_provable(
    *,
    binding_symbol_id: str,
    attribute_names: tuple[str, ...],
    index: _ProgramIndex,
) -> bool:
    """Return whether one shallow import-rooted reference is repo-provable."""
    resolved_import = index.resolved_imports_by_binding_symbol_id.get(binding_symbol_id)
    if resolved_import is None:
        return False
    if resolved_import.target_kind is ImportTargetKind.DEFINITION:
        return not attribute_names
    if resolved_import.target_kind is not ImportTargetKind.MODULE:
        return False
    if not attribute_names:
        return True

    module_qualified_name = resolved_import.target_qualified_name
    for attribute_name in attribute_names[:-1]:
        candidate_module_qualified_name = f"{module_qualified_name}.{attribute_name}"
        if candidate_module_qualified_name not in index.module_qualified_names:
            return False
        module_qualified_name = candidate_module_qualified_name

    final_qualified_name = f"{module_qualified_name}.{attribute_names[-1]}"
    return (
        final_qualified_name in index.module_qualified_names
        or final_qualified_name in index.unique_definitions_by_qualified_name
    )


def _span_starts_before(left: SourceSpan, right: SourceSpan) -> bool:
    """Return whether ``left`` starts strictly before ``right``."""
    return (left.start_line, left.start_column) < (
        right.start_line,
        right.start_column,
    )


def _span_ends_before_or_at(left: SourceSpan, right: SourceSpan) -> bool:
    """Return whether ``left`` ends before or at the start of ``right``."""
    return (left.end_line, left.end_column) <= (
        right.start_line,
        right.start_column,
    )


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
